import csv
import copy
import json
import threading
import time
from argparse import ArgumentParser

import requests
from flask import Flask, jsonify, request

INFINITY = float('inf')
MIN_PREFIX_LEN = 9

def ip_to_int(ip_str: str) -> int:
    parts = ip_str.strip().split('.')
    result = 0
    for octet in parts:
        result = (result << 8) | int(octet)
    return result

def int_to_ip(value: int) -> str:
    parts = []
    for _ in range(4):
        parts.append(str(value & 0xFF))
        value >>= 8
    return '.'.join(reversed(parts))

def parse_network(network_str: str):
    ip_part, prefix_part = network_str.split('/')
    return ip_to_int(ip_part), int(prefix_part)

def network_address(ip_int: int, prefix_len: int) -> int:
    if prefix_len <= 0:
        return 0
    if prefix_len >= 32:
        return ip_int
    mask = ((1 << 32) - 1) ^ ((1 << (32 - prefix_len)) - 1)
    return ip_int & mask

def is_valid_network_string(s: str) -> bool:
    try:
        ip_part, prefix_part = s.split('/')
        parts = ip_part.split('.')
        if len(parts) != 4:
            return False
        for p in parts:
            if not (0 <= int(p) <= 255):
                return False
        prefix = int(prefix_part)
        return 0 <= prefix <= 32
    except Exception:
        return False

def can_summarize_adjacent(net_a: str, net_b: str):
    ip_a, plen_a = parse_network(net_a)
    ip_b, plen_b = parse_network(net_b)

    if plen_a != plen_b:
        return None

    new_prefix = plen_a - 1
    if new_prefix < MIN_PREFIX_LEN:
        return None

    net_a_addr = network_address(ip_a, plen_a)
    net_b_addr = network_address(ip_b, plen_b)

    parent_a = network_address(ip_a, new_prefix)
    parent_b = network_address(ip_b, new_prefix)

    if parent_a != parent_b:
        return None

    block_size = 1 << (32 - plen_a)
    if {net_a_addr, net_b_addr} == {parent_a, parent_a + block_size}:
        return f"{int_to_ip(parent_a)}/{new_prefix}"

    return None

def apply_adjacent_summarization(table: dict) -> dict:
    changed = True
    while changed:
        changed = False
        networks = list(table.keys())

        for i in range(len(networks)):
            if networks[i] not in table:
                continue
            for j in range(i + 1, len(networks)):
                if networks[j] not in table:
                    continue

                net_a, net_b = networks[i], networks[j]

                if table[net_a]['next_hop'] != table[net_b]['next_hop']:
                    continue

                super_net = can_summarize_adjacent(net_a, net_b)
                if super_net:
                    new_cost = max(table[net_a]['cost'], table[net_b]['cost'])
                    new_hop  = table[net_a]['next_hop']

                    del table[net_a]
                    del table[net_b]
                    table[super_net] = {'cost': new_cost, 'next_hop': new_hop}
                    changed = True
                    break

            if changed:
                break

    return table

def find_common_supernet(networks: list):
    if len(networks) < 2:
        return None

    addrs = []
    for net in networks:
        ip_int, plen = parse_network(net)
        addrs.append(network_address(ip_int, plen))

    combined_diff = 0
    for addr in addrs[1:]:
        combined_diff |= (addrs[0] ^ addr)

    if combined_diff == 0:
        min_plen = min(parse_network(n)[1] for n in networks)
        if min_plen < MIN_PREFIX_LEN:
            return None
        return f"{int_to_ip(addrs[0])}/{min_plen}"

    highest_differing_bit = 0
    for bit in range(31, -1, -1):
        if (combined_diff >> bit) & 1:
            highest_differing_bit = bit
            break

    common_prefix_len = 31 - highest_differing_bit

    if common_prefix_len < MIN_PREFIX_LEN:
        return None

    supernet_addr = network_address(addrs[0], common_prefix_len)
    return f"{int_to_ip(supernet_addr)}/{common_prefix_len}"

def apply_noncontiguous_summarization(table: dict) -> dict:
    by_hop: dict = {}
    for net, info in table.items():
        hop = info['next_hop']
        by_hop.setdefault(hop, []).append(net)

    for hop, nets in by_hop.items():
        if len(nets) < 2:
            continue

        valid_nets = [n for n in nets if is_valid_network_string(n)]
        if len(valid_nets) < 2:
            continue

        super_net = find_common_supernet(valid_nets)
        if super_net is None:
            continue

        new_cost = max(table[n]['cost'] for n in valid_nets)

        for n in valid_nets:
            del table[n]
        table[super_net] = {'cost': new_cost, 'next_hop': hop}

    return table

def summarize_table_for_neighbor(routing_table: dict, neighbor_address: str,
                                  use_split_horizon: bool) -> dict:
    table = copy.deepcopy(routing_table)

    if use_split_horizon:
        table = {
            net: info
            for net, info in table.items()
            if info['next_hop'] != neighbor_address
        }

    table = apply_adjacent_summarization(table)

    table = apply_noncontiguous_summarization(table)

    return table

class Router:

    def __init__(self, my_address: str, neighbors: dict,
                 my_network: str, update_interval: int = 10,
                 split_horizon: bool = False):
        self.my_address      = my_address
        self.neighbors       = neighbors
        self.my_network      = my_network
        self.update_interval = update_interval
        self.split_horizon   = split_horizon
        self.lock            = threading.Lock()

        self.routing_table: dict = {}

        self.routing_table[self.my_network] = {
            'cost':     0,
            'next_hop': self.my_network
        }

        print("─" * 50)
        print("Tabela de roteamento inicial:")
        print(json.dumps(self.routing_table, indent=4))
        print("─" * 50)
        print(f"Split Horizon: {'ATIVADO' if self.split_horizon else 'desativado'}")
        print("─" * 50)

        self._start_periodic_updates()

    def _start_periodic_updates(self):
        thread = threading.Thread(target=self._periodic_update_loop, daemon=True)
        thread.start()

    def _periodic_update_loop(self):
        while True:
            time.sleep(self.update_interval)
            print(f"\n[{time.ctime()}] Enviando atualizações periódicas…")
            try:
                self.send_updates_to_neighbors()
            except Exception as exc:
                print(f"  Erro na atualização periódica: {exc}")

    def process_update(self, sender_address: str, sender_table: dict) -> bool:
        if sender_address not in self.neighbors:
            print(f"  [AVISO] Remetente desconhecido '{sender_address}'. Ignorando.")
            return False

        link_cost = self.neighbors[sender_address]
        changed   = False

        with self.lock:
            for network, info in sender_table.items():
                if not is_valid_network_string(network):
                    continue

                reported_cost = info.get('cost', INFINITY)

                if reported_cost == INFINITY:
                    novo_custo = INFINITY
                else:
                    novo_custo = link_cost + reported_cost

                current = self.routing_table.get(network)

                if current is None:
                    self.routing_table[network] = {
                        'cost':     novo_custo,
                        'next_hop': sender_address
                    }
                    changed = True
                    print(f"  [+] Nova rota    {network:<22} custo={novo_custo:<6} via {sender_address}")

                elif novo_custo < current['cost']:
                    self.routing_table[network] = {
                        'cost':     novo_custo,
                        'next_hop': sender_address
                    }
                    changed = True
                    print(f"  [~] Rota melhor  {network:<22} custo={current['cost']}->{novo_custo:<6} via {sender_address}")

                elif current['next_hop'] == sender_address and current['cost'] != novo_custo:
                    self.routing_table[network] = {
                        'cost':     novo_custo,
                        'next_hop': sender_address
                    }
                    changed = True
                    print(f"  [!] Custo mudou  {network:<22} custo={current['cost']}->{novo_custo:<6} via {sender_address}")

        if changed:
            print("\nTabela atualizada:")
            print(json.dumps(self.routing_table, indent=4))

        return changed

    def send_updates_to_neighbors(self):
        with self.lock:
            table_snapshot = copy.deepcopy(self.routing_table)

        for neighbor_address in self.neighbors:
            tabela_para_enviar = summarize_table_for_neighbor(
                table_snapshot,
                neighbor_address,
                self.split_horizon
            )

            payload = {
                "sender_address": self.my_address,
                "routing_table":  tabela_para_enviar
            }

            url = f'http://{neighbor_address}/receive_update'
            try:
                print(f"  → Enviando para {neighbor_address} "
                      f"({len(tabela_para_enviar)} rotas "
                      f"{'[SH]' if self.split_horizon else ''})")
                requests.post(url, json=payload, timeout=5)
            except requests.exceptions.RequestException as exc:
                print(f"  ✗ Falha ao conectar em {neighbor_address}: {exc}")

app             = Flask(__name__)
router_instance: Router = None

@app.route('/routes', methods=['GET'])
def get_routes():
    if router_instance is None:
        return jsonify({"error": "Roteador não inicializado"}), 500

    with router_instance.lock:
        table_snapshot = copy.deepcopy(router_instance.routing_table)

    return jsonify({
        "my_address":      router_instance.my_address,
        "my_network":      router_instance.my_network,
        "split_horizon":   router_instance.split_horizon,
        "vizinhos":        router_instance.neighbors,
        "update_interval": router_instance.update_interval,
        "routing_table":   table_snapshot
    })

@app.route('/receive_update', methods=['POST'])
def receive_update():
    if not request.json:
        return jsonify({"error": "Body must be JSON"}), 400

    data           = request.json
    sender_address = data.get("sender_address")
    sender_table   = data.get("routing_table")

    if not sender_address or not isinstance(sender_table, dict):
        return jsonify({"error": "sender_address e routing_table são obrigatórios"}), 400

    print(f"\n← Recebida atualização de {sender_address} ({len(sender_table)} rotas)")

    changed = router_instance.process_update(sender_address, sender_table)

    return jsonify({
        "status":        "success",
        "message":       "Update received",
        "table_changed": changed
    }), 200

if __name__ == '__main__':
    parser = ArgumentParser(
        description="Roteador Vetor de Distância — Grupo 3 (Dual Ring)"
    )
    parser.add_argument('-p', '--port', type=int, default=5000,
                        help="Porta para o servidor Flask (padrão: 5000)")
    parser.add_argument('-f', '--file', type=str, required=True,
                        help="CSV com vizinhos: colunas 'vizinho,custo' ou 'neighbor_address,cost'")
    parser.add_argument('--network', type=str, required=True,
                        help="Rede administrada diretamente (ex: 10.0.1.0/24)")
    parser.add_argument('--interval', type=int, default=10,
                        help="Intervalo entre atualizações (s, padrão: 10)")
    parser.add_argument('--split-horizon', dest='split_horizon',
                        action='store_true', default=False,
                        help="Ativa Split Horizon para evitar contagem ao infinito")
    parser.add_argument('--address', type=str, default=None,
                        help="IP real desta máquina (ex: 192.168.0.3). "
                             "Necessário no lab com múltiplas máquinas. "
                             "Padrão: 127.0.0.1")
    args = parser.parse_args()

    neighbors_config: dict = {}
    try:
        with open(args.file, mode='r', newline='') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames or []
            if 'vizinho' in fieldnames:
                col_addr, col_cost = 'vizinho', 'custo'
            elif 'neighbor_address' in fieldnames:
                col_addr, col_cost = 'neighbor_address', 'cost'
            else:
                print(f"Erro: CSV deve ter 'vizinho,custo' ou 'neighbor_address,cost'. "
                      f"Encontrado: {fieldnames}")
                exit(1)

            for row in reader:
                addr = row[col_addr].strip()
                cost = int(row[col_cost].strip())
                neighbors_config[addr] = cost

    except FileNotFoundError:
        print(f"Erro: Arquivo '{args.file}' não encontrado.")
        exit(1)
    except (KeyError, ValueError) as exc:
        print(f"Erro ao ler CSV: {exc}")
        exit(1)

    host_ip = args.address if args.address else "127.0.0.1"
    my_full_address = f"{host_ip}:{args.port}"

    print("=" * 50)
    print("  ROTEADOR — GRUPO 3 / DUAL RING")
    print("=" * 50)
    print(f"  Endereço  : {my_full_address}")
    print(f"  Rede      : {args.network}")
    print(f"  Vizinhos  : {neighbors_config}")
    print(f"  Intervalo : {args.interval}s")
    print(f"  Split Hz  : {'SIM' if args.split_horizon else 'NÃO'}")
    print("=" * 50)

    router_instance = Router(
        my_address      = my_full_address,
        neighbors       = neighbors_config,
        my_network      = args.network,
        update_interval = args.interval,
        split_horizon   = args.split_horizon
    )

    app.run(host='0.0.0.0', port=args.port, debug=False)
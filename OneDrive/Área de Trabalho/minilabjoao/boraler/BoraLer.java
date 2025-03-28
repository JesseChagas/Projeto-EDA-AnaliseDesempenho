import java.util.*;

class BoraLer {
    private Map<String, IndicacaoLeitura> indicacoes;

    /**
     * Construtor da classe BoraLer.
     * Inicializa a estrutura de armazenamento das indicações de leitura.
     */
    public BoraLer() {
        this.indicacoes = new HashMap<>();
    }

    /**
     * Cadastra uma nova indicação de leitura, garantindo que o título seja único.
     *
     * @param titulo    O título do livro.
     * @param descricao A descrição do livro.
     * @param autor     O nome de quem fez a indicação.
     * @throws IllegalArgumentException Se já existir uma indicação com o mesmo título.
     */
    public void cadastrarIndicacaoLeitura(String titulo, String descricao, String autor) {
        if (indicacoes.containsKey(titulo)) {
            throw new IllegalArgumentException("Indicação de leitura já cadastrada.");
        }
        indicacoes.put(titulo, new IndicacaoLeitura(titulo, descricao, autor));
    }

    /**
     * Retorna a recomendação de leitura baseada na indicação mais favoritada.
     *
     * @return Informações do livro mais favoritado ou mensagem caso não haja indicações.
     */
    public String recomendar() {
        return indicacoes.values().stream()
                .max(Comparator.comparingInt(IndicacaoLeitura::getFavoritado))
                .map(l -> "Título: " + l.getTitulo() + "\nDescrição: " + l.getDescricao() +
                        "\nAutor: " + l.getAutor() + "\nFavoritos: " + l.getFavoritado())
                .orElse("Nenhuma indicação disponível.");
    }

    /**
     * Marca uma indicação de leitura como favorita, aumentando sua popularidade.
     *
     * @param titulo O título do livro a ser favoritado.
     * @throws IllegalArgumentException Se o título não for encontrado.
     */
    public void favoritar(String titulo) {
        IndicacaoLeitura livro = indicacoes.get(titulo);
        if (livro == null) {
            throw new IllegalArgumentException("Indicação de leitura não encontrada.");
        }
        livro.incrementarFavoritos();
    }

    /**
     * Avalia uma indicação de leitura com uma nota e um comentário.
     *
     * @param titulo    O título do livro a ser avaliado.
     * @param nota      A nota da avaliação (1 a 5).
     * @param comentario O comentário da avaliação.
     * @throws IllegalArgumentException Se o título não for encontrado ou nota inválida.
     */
    public void avaliar(String titulo, int nota, String comentario) {
        IndicacaoLeitura livro = indicacoes.get(titulo);
        if (livro == null) {
            throw new IllegalArgumentException("Indicação de leitura não encontrada.");
        }
        if (nota < 1 || nota > 5) {
            throw new IllegalArgumentException("Nota inválida. Deve estar entre 1 e 5.");
        }
        livro.avaliar(nota, comentario);
    }

    /**
     * Exibe as informações de uma indicação de leitura, incluindo a última avaliação.
     *
     * @param titulo O título do livro a ser exibido.
     * @return Informações sobre a indicação.
     * @throws IllegalArgumentException Se o título não for encontrado.
     */
    public String exibirIndicacaoLeitura(String titulo) {
        IndicacaoLeitura livro = indicacoes.get(titulo);
        if (livro == null) {
            throw new IllegalArgumentException("Indicação de leitura não encontrada.");
        }
        StringBuilder sb = new StringBuilder();
        sb.append("Título: ").append(livro.getTitulo())
          .append("\nDescrição: ").append(livro.getDescricao())
          .append("\nAutor: ").append(livro.getAutor())
          .append("\nFavoritos: ").append(livro.getFavoritado());

        if (livro.getAvaliacaoMaisRecente() != null) {
            sb.append("\nÚltima Avaliação: Nota ").append(livro.getAvaliacaoMaisRecente().getNota())
              .append(" - ").append(livro.getAvaliacaoMaisRecente().getComentario());
        }
        return sb.toString();
    }
}

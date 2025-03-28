class IndicacaoLeitura {
    private String titulo;
    private String descricao;
    private String autor;
    private int favoritado;
    private Avaliacao avaliacaoMaisRecente;

    /**
     * Construtor da classe IndicacaoLeitura.
     *
     * @param titulo    O título do livro.
     * @param descricao A descrição do livro.
     * @param autor     O nome de quem fez a indicação.
     */
    public IndicacaoLeitura(String titulo, String descricao, String autor) {
        this.titulo = titulo;
        this.descricao = descricao;
        this.autor = autor;
        this.favoritado = 0;
        this.avaliacaoMaisRecente = null;
    }

    public String getTitulo() {
        return titulo;
    }

    public String getDescricao() {
        return descricao;
    }

    public String getAutor() {
        return autor;
    }

    public int getFavoritado() {
        return favoritado;
    }

    public Avaliacao getAvaliacaoMaisRecente() {
        return avaliacaoMaisRecente;
    }

    /**
     * Incrementa o número de favoritos para essa indicação.
     */
    public void incrementarFavoritos() {
        this.favoritado++;
    }

    /**
     * Registra uma avaliação para esta indicação de leitura.
     *
     * @param nota      Nota da avaliação (1 a 5).
     * @param comentario Comentário sobre a leitura.
     */
    public void avaliar(int nota, String comentario) {
        this.avaliacaoMaisRecente = new Avaliacao(nota, comentario);
    }
}

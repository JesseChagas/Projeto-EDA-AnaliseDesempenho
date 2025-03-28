class Avaliacao {
    private int nota;
    private String comentario;

    /**
     * Construtor da classe Avaliacao.
     *
     * @param nota      Nota dada para a leitura (de 1 a 5).
     * @param comentario Comentário sobre a leitura.
     */
    public Avaliacao(int nota, String comentario) {
        this.nota = nota;
        this.comentario = comentario;
    }

    public int getNota() {
        return nota;
    }

    public String getComentario() {
        return comentario;
    }
}

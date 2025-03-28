import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class BoraLerTest {
    private BoraLer boraLer;

    @BeforeEach
    void setUp() {
        boraLer = new BoraLer();
    }

    @Test
    void testCadastrarIndicacaoLeitura() {
        boraLer.cadastrarIndicacaoLeitura("Livro A", "Descrição A", "Autor A");
        assertThrows(IllegalArgumentException.class, () -> 
            boraLer.cadastrarIndicacaoLeitura("Livro A", "Outra Descrição", "Outro Autor"),
            "Deveria lançar exceção ao cadastrar título duplicado"
        );
    }

    @Test
    void testRecomendarSemIndicacoes() {
        assertEquals("Nenhuma indicação disponível.", boraLer.recomendar());
    }

    @Test
    void testRecomendarComUmaIndicacao() {
        boraLer.cadastrarIndicacaoLeitura("Livro A", "Descrição A", "Autor A");
        String esperado = "Título: Livro A\nDescrição: Descrição A\nAutor: Autor A\nFavoritos: 0";
        assertEquals(esperado, boraLer.recomendar());
    }

    @Test
    void testRecomendarComFavoritos() {
        boraLer.cadastrarIndicacaoLeitura("Livro A", "Descrição A", "Autor A");
        boraLer.cadastrarIndicacaoLeitura("Livro B", "Descrição B", "Autor B");
        
        boraLer.favoritar("Livro B");
        boraLer.favoritar("Livro B");
        boraLer.favoritar("Livro A");

        String esperado = "Título: Livro B\nDescrição: Descrição B\nAutor: Autor B\nFavoritos: 2";
        assertEquals(esperado, boraLer.recomendar());
    }

    @Test
    void testFavoritarIndicacao() {
        boraLer.cadastrarIndicacaoLeitura("Livro A", "Descrição A", "Autor A");
        boraLer.favoritar("Livro A");
        String esperado = "Título: Livro A\nDescrição: Descrição A\nAutor: Autor A\nFavoritos: 1";
        assertEquals(esperado, boraLer.recomendar());
    }

    @Test
    void testFavoritarIndicacaoInexistente() {
        assertThrows(IllegalArgumentException.class, () -> 
            boraLer.favoritar("Livro X"),
            "Deveria lançar exceção ao favoritar um livro inexistente"
        );
    }

    @Test
    void testAvaliarIndicacao() {
        boraLer.cadastrarIndicacaoLeitura("Livro A", "Descrição A", "Autor A");
        boraLer.avaliar("Livro A", 5, "Ótimo livro!");

        String esperado = "Título: Livro A\nDescrição: Descrição A\nAutor: Autor A\nFavoritos: 0\nÚltima Avaliação: Nota 5 - Ótimo livro!";
        assertEquals(esperado, boraLer.exibirIndicacaoLeitura("Livro A"));
    }

    @Test
    void testAvaliarIndicacaoInexistente() {
        assertThrows(IllegalArgumentException.class, () -> 
            boraLer.avaliar("Livro X", 4, "Muito bom!"),
            "Deveria lançar exceção ao avaliar um livro inexistente"
        );
    }

    @Test
    void testAvaliarComNotaInvalida() {
        boraLer.cadastrarIndicacaoLeitura("Livro A", "Descrição A", "Autor A");

        assertThrows(IllegalArgumentException.class, () -> 
            boraLer.avaliar("Livro A", 0, "Nota inválida!"),
            "Deveria lançar exceção para nota menor que 1"
        );

        assertThrows(IllegalArgumentException.class, () -> 
            boraLer.avaliar("Livro A", 6, "Nota inválida!"),
            "Deveria lançar exceção para nota maior que 5"
        );
    }
}

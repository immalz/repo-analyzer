import unittest

import builders  # noqa: F401  (configura el path de src/)

from engine.conditions import evaluate_condition

VALUES = {"violations": 5, "present": True, "portability": "CLOUD_SPECIFIC", "ratio": 0.65, "delta": -1}


class EvaluateConditionTest(unittest.TestCase):
    def test_cumple_menor_o_igual_en_el_limite(self):
        self.assertTrue(evaluate_condition("violations <= 5", VALUES))

    def test_no_cumple_menor_estricto_en_el_limite(self):
        self.assertFalse(evaluate_condition("violations < 5", VALUES))

    def test_acepta_operador_sin_espacios(self):
        self.assertTrue(evaluate_condition("violations>=5", VALUES))

    def test_interpreta_true_como_booleano(self):
        self.assertTrue(evaluate_condition("present == true", VALUES))

    def test_compara_textos_entre_comillas(self):
        self.assertFalse(evaluate_condition('portability != "CLOUD_SPECIFIC"', VALUES))

    def test_compara_decimales(self):
        self.assertTrue(evaluate_condition("ratio < 0.7", VALUES))

    def test_compara_negativos(self):
        self.assertTrue(evaluate_condition("delta > -2", VALUES))

    def test_metrica_ausente_nunca_cumple(self):
        self.assertFalse(evaluate_condition("missing == 0", VALUES))

    def test_operador_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            evaluate_condition("violations ~ 1", VALUES)


if __name__ == "__main__":
    unittest.main()

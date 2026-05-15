import json

class SaveManager:

    @staticmethod
    def guardar(game_state):

        data = {
            "vidas": game_state.vidas,
            "nivel_actual": game_state.nivel_actual,
            "ult_nivel_desbloqueado": game_state.ult_nivel_desbloqueado,
            "puntos": game_state.puntos
        }

        with open("data/save.json", "w") as file:
            json.dump(data, file, indent=4)

    @staticmethod
    def cargar(game_state):

        try:
            with open("data/save.json", "r") as file:
                data = json.load(file)

                game_state.vidas = data["vidas"]
                game_state.nivel_actual = data["nivel_actual"]
                game_state.ult_nivel_desbloqueado = data["ult_nivel_desbloqueado"]
                game_state.puntos = data["puntos"]

        except FileNotFoundError:
            print("No existe save")
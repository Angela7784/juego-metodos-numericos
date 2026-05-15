            nivel = level_manager.get_level(game_state.nivel_actual)

            mostrar_mapa(
                screen,
                WIDTH,
                HEIGHT,
                font_title,
                font_button,
                WHITE,
                DARK_GREY,
                event,
                mouse_pos,
                game_state,
                nivel
            )
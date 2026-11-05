# Ferramentas Runa Verde

Scripts de referência usados para criar fotos e vídeos dos anúncios.

- `recorte_fotos.py` – fundo branco: máscara do modelo isnet + máscara de cor, contorno simplificado (approxPolyDP) e suavizado em 4x. As linhas `pts=` cortam sombras específicas de cada foto: ajuste por foto.
- `cena_mesa_mistica.py` – mesa mística procedural (roxo, dourado, cobre, velas, cristais, bola de cristal, cartas, círculo de runas girando).
- `video_mistico.py` – vídeo de 24 s (vertical `v` ou quadrado `sq`; terceiro argumento gera só prévia). Usa os recortes `obj*.png`.
- `musica_mistica.py` – trilha mística (coro, handpan, tambor xamânico, tigela tibetana, harpa).

![Header](https://user-images.githubusercontent.com/24854541/100174337-fbdfd380-2eaa-11eb-8904-ed9879116bc8.png)

A densidade da mama é comprovadamente relacionada com o risco do desenvolvimento de câncer, uma vez que mulheres com uma maior densidade mamária podem esconder lesões, levando o câncer a ser detectado tardiamente. A escalade densidade chamada BIRADS foi desenvolvida pelo American College of Radiology e informa os radiologistas sobre a diminuição da sensibilidade do exame com o aumento da densidade da mama. BI-RADS definem a densidade como sendo quase inteiramente composta por gordura (densidade I), por tecido fibrobroglandular difuso (densidade II), por tecido denso heterogêneo (III) e portecido extremamente denso (IV). A mamografia é a principal ferramenta derastreio do câncer e radiologistas avaliam a densidade da mama com base na análise visual das imagens.

O objetivo desse projeto é desenvolver um programa capaz de classificar a densidade das mamas na escala BIRADS através das imagens fornecidas.

# Técnicas Implementadas

Para a classificação utilizamos as seguintes características de imagens:

- Energia
- Entropia
- Homogeneidade
- Contraste
- Momentos invariantes de Hu

Com essa características, utilizamos a distância de Mahalanobis para classificar as imagens na escala BIRADS.

# Instalando as Dependências

1. Clone esse repositório:
```shell
git clone https://github.com/viniciusvviterbo/Agnitio
```

2. (Opcional) Crie um ambiente virtual:
```shell
virtualenv .venv
source .venv/bin/activate
```

3. Instale as dependências:
```shell
pip3 install -r requirements.txt
```

# Uso

```
python3 agnitio.py
```

# Autores
[Erick Lage](https://github.com/erickLage)

[Vinícius Viterbo](https://github.com/viniciusvviterbo)

![Separador](https://user-images.githubusercontent.com/24854541/100174347-05693b80-2eab-11eb-9fd9-9662153767c0.png)

**[GNU AGPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html)**

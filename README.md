![Header](https://user-images.githubusercontent.com/24854541/100174337-fbdfd380-2eaa-11eb-8904-ed9879116bc8.png)

*Leia esse README em [`português`](https://github.com/viniciusvviterbo/Agnitio/blob/main/README.pt.md).*

Breast density is proven to be related to the risk of developing cancer, since women with a higher breast density can hide lesions, leading to cancer being detected late. The density scale called BIRADS was developed by the American College of Radiology and informs radiologists about the decrease in the sensitivity of the exam with increasing breast density. BI-RADS define density as being almost entirely composed of fat (density I), diffuse fibrobroglandular tissue (density II), heterogeneous dense tissue (III) and extremely dense (IV). Mammography is the main cancer screening tool and radiologists assess breast density based on visual analysis of the images.

The objective of this project is to develop a program capable of classifying breast density on the BIRADS scale through the images provided.

# Implemented Techniques

For the classification the following image characteristics were used:

- Energy
- Entropy
- Homogeneity
- Contrast
- Hu's invariant moments

With these characteristics, we used the Mahalanobis distance to classify the images on the BIRADS scale.

# Installing Dependencies

1. Clone this repository:
```shell
git clone https://github.com/viniciusvviterbo/Agnitio
```

2. (Optional) Create a virtual environment:
```shell
virtualenv .venv
source .venv/bin/activate
```

3. Install the dependencies:
```shell
pip3 install -r requirements.txt
```

# Usage

```
python3 agnitio.py
```

# Authors
[Erick Lage](https://github.com/erickLage)

[Vinícius Viterbo](https://github.com/viniciusvviterbo)

![Separador](https://user-images.githubusercontent.com/24854541/100174347-05693b80-2eab-11eb-9fd9-9662153767c0.png)

**[GNU AGPL v3.0](https://www.gnu.org/licenses/gpl-3.0.html)**

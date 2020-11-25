from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from skimage.feature import greycomatrix, greycoprops
from skimage.measure import moments_hu, shannon_entropy
import cv2
import numpy as np
from PIL import ImageTk, Image
from pathlib import Path
import os
import sys
import random
from timeit import default_timer as timer

inicioExecucaoTreino = float()
fimExecucaoTreino = float()

inicioExecucaoImagemTotal = float()
fimExecucaoImagemTotal = float()

inicioExecucaoImagemSelecionada = float()
fimExecucaoImagemSelecionada = float()

class AutoScrollbar(Scrollbar):
    def set(self, lo, hi):
        # Caso a escala do canvas exibido seja menor que 1, remove as barras  
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise TclError('Não se pode usar .pack com esse widget')

    def place(self, **kw):
        raise TclError('Não se pode usar .place com esse widget')

class Aplicacao(Frame):
    def __init__(self, master=None, titulo=''):
        super().__init__(master)
        self.master = master

        ### ATRIBUTOS ###
        self.master.title(titulo) # Título da imagem
        self.imagem = None # Instancia da imagem original
        self.pathImagem = None
        self.janela_largura, self.janela_altura = self.getResolucaoTela() # Define as dimensões da janela
        
        self.canvas = None # Instancia da área de manipulação da imagem
        self.textoAncora = None # Define o texto que será usado como referência de instanciação da imagem
        self.imagemModificada = None # Instância do objeto manipulável que representa a imagem original
        self.coordImagem = None # Instancia das coordenadas da imagem
        self.coordClickOrigem = None
        self.coordClickDestino = None
        self.areaSelecionada = None # Define a area selecionada (quadrado verde)
        
        self.imagensTreinamento = [list(),list(),list(),list()] # Define o vetor que armazenará as imagens que serão utilizadas para treinamento

        self.matrizConfusao = None

        self.opcaoEntropia = BooleanVar(value=True) # Define o valor das opções selecionadas na janela de seleção de características
        self.opcaoHomogeneidade = BooleanVar(value=True) # Define o valor das opções selecionadas na janela de seleção de características
        self.opcaoEnergia = BooleanVar(value=True) # Define o valor das opções selecionadas na janela de seleção de características
        self.opcaoContraste = BooleanVar(value=True) # Define o valor das opções selecionadas na janela de seleção de características
        self.opcaoHu =  BooleanVar(value=True) # Define o valor das opções selecionadas na janela de seleção de características

        self.caracteristicasImagens = [list(),list(),list(),list()] # Define uma matriz onde cada linha corresponde às características de um diretório
        self.caracteristicasImagensTeste = [list(),list(),list(),list()] # Define uma matriz onde cada linha corresponde às características de um diretório
        
        # Aplica as dimensões e posição da janela
        self.master.geometry(str(self.janela_largura) + 'x' + str(self.janela_altura) + '+0+0')
        # Implementa o menu e seus componentes na janela
        self.criarMenu()

    # Obtêm as dimensões da tela
    def getResolucaoTela(self):
        tela_largura = self.master.winfo_screenwidth()
        tela_altura = self.master.winfo_screenheight()
        return (tela_largura, tela_altura)

    # Abre uma imagem na tela
    def abrirImagem(self):
        # Abre caixa de diálogo para seleção do arquivo
        fname = filedialog.askopenfilename(title='Selecione imagem para manipulação')
        # Garante que um arquivo foi escolhido
        if type(fname) is str and fname != '':
            # Implementa barras de rolagem vertical e horizontal para o canvas
            vScrollBar = AutoScrollbar(self.master, orient='vertical')
            hScrollBar = AutoScrollbar(self.master, orient='horizontal')
            vScrollBar.grid(row=0, column=1, sticky='ns')
            hScrollBar.grid(row=1, column=0, sticky='we')

            # Instancia a imagem selecionada
            self.imagem = Image.open(fname)
            self.pathImagem = fname
            self.coordImagem = (0, 0)

            # Instancia o canvas
            self.canvas = Canvas(self.master, highlightthickness=0, xscrollcommand=hScrollBar.set, yscrollcommand=vScrollBar.set)
            self.canvas.grid(row=0, column=0, sticky='nswe')

            # Vincula as barras de rolagem com o canvas
            vScrollBar.configure(command=self.canvas.yview)
            hScrollBar.configure(command=self.canvas.xview)
            
            # Faz do canvas expandível
            self.master.rowconfigure(0, weight=1)
            self.master.columnconfigure(0, weight=1)

            # Vincula os botões de interação com funções do código
            self.vincularBotoes()

            self.imagemEscala = 1.0 # Define a escala de exibição da imagem
            self.imagemId = None # Define o id da imagem
            self.delta = 0.75 # Define a constante que será usada para a alteração da escala da imagem no zoom 

            imagemLargura, imagemAltura = self.imagem.size
                                            
            # Text é usado para configurar propriamente as coordenadas da imagem
            self.textoAncora = self.canvas.create_text(0, 0, anchor='nw', text='Scroll to zoom')
            
            # Exibe a imagem no canvas
            self.mostrarImagem()
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        else:
            return

    # Abre um diretório enewImg lê todas as imagens em seus subdiretórios
    def lerDiretorio(self):
        self.imagensTreinamento = [list(),list(),list(),list()]

        inicioExecucaoTreino = timer()

        # Lê o caminho do diretório escolhido pelo usuário
        caminhoDir = filedialog.askdirectory(title='Selecione o diretório de treinamento')
        # Garante que um diretório foi escolhido
        if type(caminhoDir) is str and caminhoDir != '':
            # Declara a lista de imagens (e dados relacionado) que serão utilizadas para treinamento
            # Cada tupla nesse array será composto como (CAMINHO_DA_IMG, NOME_IMG, PASTA_ORIGEM_IMG)
            # Loop para cada item encontrado no caminho selecionado
            for item in os.listdir(caminhoDir):
                # Caso o item da iteração NÃO seja um arquivo (ou seja, um subdiretório), executa
                if os.path.isfile(os.path.join(caminhoDir, item)) is False:
                    # Adiciona o nome dos arquivos do subdiretório à lista
                    for img in os.listdir(os.path.join(caminhoDir, item)):
                        caminhoImagem = os.path.join(caminhoDir, item) + '/' + img
                        tmp = (caminhoImagem, cv2.imread(caminhoImagem, 0))
                        self.imagensTreinamento[int(item) - 1].append(tmp)
                        
            # Inicializa o treina do classificador de imagens
            self.treinarClassificador()

        else:
            return

    # Reliza o treino do classificador de imagens
    def treinarClassificador(self):
        self.caracteristicasImagens = [list(),list(),list(),list()]
        self.caracteristicasImagensTeste = [list(),list(),list(),list()]

        # Instancia matrizes de medias, cada posição sendo uma média para cada diretório
        mediaContraste = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]
        mediaHomogeneidade = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]
        mediaEnergia = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]
        mediaEntropia = [[0],[0],[0],[0]]
        mediaHu = [[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0],[0,0,0,0,0,0,0]]

        listaCaracteristicasImagens = list()
        listaCaracteristicasImagensTeste = list()

        contraste = [0,0,0,0,0]
        homogeneidade = [0,0,0,0,0]
        energia = [0,0,0,0,0]
        entropia = [0]
        hu = [0,0,0,0,0,0,0]

        for pasta in self.imagensTreinamento: # Para cada array em self.imagensTreinamento
            random.shuffle(pasta) # Embaralha a ordem das tuplas nesse array
            for img in pasta[:round(len(pasta)*0.75)]: # Para as tuplas dentre as 75% primeiras da lista, executa
                im = img[1] # Instancia o cv2.imread da imagem referenciada
                data = np.array((im/8), 'int') # Divide os valores de cinza de im em 8 para que existam no máximo 32 tons de cinza
                g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32, normed=True, symmetric=True) # Calcula a matrix de co-ocorrência do nível de cinza da imagem.
                
                # Obtêm-se as características selecionadas pelo usuário
                if self.opcaoContraste.get():    
                    contraste = greycoprops(g, 'contrast') # Calcula o contraste da matrix de co-ocorrência de níveis de cinza
                    contraste = [sum(i) for i in contraste]
                    mediaContraste[self.imagensTreinamento.index(pasta)] = np.add(mediaContraste[self.imagensTreinamento.index(pasta)], contraste)
                if self.opcaoHomogeneidade.get():
                    homogeneidade = greycoprops(g, 'homogeneity') # Calcula a homogeneidade da matrix de co-ocorrência de níveis de cinza
                    homogeneidade = [sum(i) for i in homogeneidade]
                    mediaHomogeneidade[self.imagensTreinamento.index(pasta)] = np.add(mediaHomogeneidade[self.imagensTreinamento.index(pasta)], homogeneidade)
                if self.opcaoEnergia.get():
                    energia = greycoprops(g, 'energy') # Calcula a energia da matrix de co-ocorrência de níveis de cinza
                    energia = [sum(i) for i in energia]
                    mediaEnergia[self.imagensTreinamento.index(pasta)] = np.add(mediaEnergia[self.imagensTreinamento.index(pasta)], energia)
                if self.opcaoEntropia.get():
                    entropia = shannon_entropy(data) # Calcula a entropia de Shannon da imagem
                    mediaEntropia[self.imagensTreinamento.index(pasta)] = np.add(mediaEntropia[self.imagensTreinamento.index(pasta)], entropia)
                if self.opcaoHu.get():
                    hu = moments_hu(data) # Calcula os movimentos de Hu da imagem
                    mediaHu[self.imagensTreinamento.index(pasta)] = np.add(mediaHu[self.imagensTreinamento.index(pasta)], hu)

                self.caracteristicasImagens[self.imagensTreinamento.index(pasta)].append([contraste, homogeneidade, energia, entropia, hu])
            
            # Para obter o valor médio das características, divide-se pelo número de itens adicionados
            mediaContraste[self.imagensTreinamento.index(pasta)]      /= round(len(pasta)*0.75)
            mediaHomogeneidade[self.imagensTreinamento.index(pasta)]  /= round(len(pasta)*0.75)
            mediaEnergia[self.imagensTreinamento.index(pasta)]        /= round(len(pasta)*0.75)
            mediaEntropia[self.imagensTreinamento.index(pasta)]       /= round(len(pasta)*0.75)
            mediaHu[self.imagensTreinamento.index(pasta)]             /= round(len(pasta)*0.75)

            # Transforma as características de self.caracteristicasImagens[self.imagensTreinamento.index(pasta)] em médias centradas
            for caracteristicaImg in self.caracteristicasImagens[self.imagensTreinamento.index(pasta)]:    
                caracteristicaImg[0] = np.subtract(caracteristicaImg[0], mediaContraste[self.imagensTreinamento.index(pasta)])
                caracteristicaImg[1] = np.subtract(caracteristicaImg[1], mediaHomogeneidade[self.imagensTreinamento.index(pasta)])
                caracteristicaImg[2] = np.subtract(caracteristicaImg[2], mediaEnergia[self.imagensTreinamento.index(pasta)])
                caracteristicaImg[3] = np.subtract(caracteristicaImg[3], mediaEntropia[self.imagensTreinamento.index(pasta)])
                caracteristicaImg[4] = np.subtract(caracteristicaImg[4], mediaHu[self.imagensTreinamento.index(pasta)])
                
                caracteristicaImg = caracteristicaImg[5:]

            # Rearraja os dados obtidos em uma lista, onde cada linha é um array ordenado de todas as características
            listaCaracteristicasPasta = list()
            for tupla in self.caracteristicasImagens[self.imagensTreinamento.index(pasta)]:
                caracteristicasImagem = np.ndarray(shape=(0,0))
                for caracteristica in tupla:
                    caracteristicasImagem = np.concatenate((caracteristicasImagem, caracteristica), axis=None)
                listaCaracteristicasPasta.append(caracteristicasImagem)
            # Adiciona essa lista ao conjunto de listas dos demais diretórios
            listaCaracteristicasImagens.append(listaCaracteristicasPasta)
            
        # Declara as matrizes de covariância de cada diretório
        matrizCovariancia1 = np.cov(np.array(listaCaracteristicasImagens[0]).T)
        matrizCovariancia2 = np.cov(np.array(listaCaracteristicasImagens[1]).T)
        matrizCovariancia3 = np.cov(np.array(listaCaracteristicasImagens[2]).T)
        matrizCovariancia4 = np.cov(np.array(listaCaracteristicasImagens[3]).T)
        
        # Obtêm as matrizes inversas das de covariância dos diretórios
        self.inversoCovariancia1 = np.linalg.inv(matrizCovariancia1)
        self.inversoCovariancia2 = np.linalg.inv(matrizCovariancia2)
        self.inversoCovariancia3 = np.linalg.inv(matrizCovariancia3)
        self.inversoCovariancia4 = np.linalg.inv(matrizCovariancia4)

        self.media1 = np.concatenate((mediaContraste[0], mediaHomogeneidade[0], mediaEnergia[0], mediaEntropia[0], mediaHu[0]), axis=None) 
        self.media2 = np.concatenate((mediaContraste[1], mediaHomogeneidade[1], mediaEnergia[1], mediaEntropia[1], mediaHu[1]), axis=None) 
        self.media3 = np.concatenate((mediaContraste[2], mediaHomogeneidade[2], mediaEnergia[2], mediaEntropia[2], mediaHu[2]), axis=None) 
        self.media4 = np.concatenate((mediaContraste[3], mediaHomogeneidade[3], mediaEnergia[3], mediaEntropia[3], mediaHu[3]), axis=None) 
        
        # Matriz Confusão
        matrizConfusao = [[0, 0, 0, 0],[0, 0, 0, 0],[0, 0, 0, 0],[0, 0, 0, 0]]
        for pasta in self.imagensTreinamento: # Para cada array em self.imagensTreinamento
            for img in pasta[round(len(pasta)*0.75):]: # Para as tuplas dentre as 25% últimas da lista, executa
                im = img[1] # Instancia o cv2.imread da imagem referenciada
                data = np.array((im/8), 'int') # Divide os valores de cinza de im em 8 para que existam no máximo 32 tons de cinza
                g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32, normed=True, symmetric=True) # Calcula a matrix de co-ocorrência do nível de cinza da imagem.
                
                # Obtêm-se as características selecionadas pelo usuário
                if self.opcaoContraste:    
                    contraste = greycoprops(g, 'contrast') # Calcula o contraste da matrix de co-ocorrência de níveis de cinza
                    contraste = [sum(i) for i in contraste]
                if self.opcaoHomogeneidade:
                    homogeneidade = greycoprops(g, 'homogeneity') # Calcula a homogeneidade da matrix de co-ocorrência de níveis de cinza
                    homogeneidade = [sum(i) for i in homogeneidade]
                if self.opcaoEnergia:
                    energia = greycoprops(g, 'energy') # Calcula a energia da matrix de co-ocorrência de níveis de cinza
                    energia = [sum(i) for i in energia]
                if self.opcaoEntropia:
                    entropia = shannon_entropy(data) # Calcula a entropia de Shannon da imagem
                if self.opcaoHu:
                    hu = moments_hu(data) # Calcula os movimentos de Hu da imagem
                    
                self.caracteristicasImagensTeste[self.imagensTreinamento.index(pasta)].append([contraste, homogeneidade, energia, entropia, hu])
            
            # Rearraja os dados obtidos em uma lista, onde cada linha é um array ordenado de todas as características
            listaCaracteristicasTestePasta = list()
            for tupla in self.caracteristicasImagensTeste[self.imagensTreinamento.index(pasta)]:
                caracteristicasImagemTeste = np.ndarray(shape=(0,0))
                for caracteristicaTeste in tupla:
                    caracteristicasImagemTeste = np.concatenate((caracteristicasImagemTeste, caracteristicaTeste), axis=None)
                listaCaracteristicasTestePasta.append(caracteristicasImagemTeste)
            # Adiciona essa lista ao conjunto de listas dos demais diretórios
            listaCaracteristicasImagensTeste.append(listaCaracteristicasTestePasta)
        
            #for img in pasta[round(len(pasta)*0.75):]: # Para as tuplas dentre as 25% últimas da lista, executa
            for i in range(75, 100): # Para as tuplas dentre as 25% últimas da lista, executa
                listaDiferencialTeste1 = np.subtract(listaCaracteristicasTestePasta[i - 75], self.media1)
                listaDiferencialTeste2 = np.subtract(listaCaracteristicasTestePasta[i - 75], self.media2)
                listaDiferencialTeste3 = np.subtract(listaCaracteristicasTestePasta[i - 75], self.media3)
                listaDiferencialTeste4 = np.subtract(listaCaracteristicasTestePasta[i - 75], self.media4)

                dist1 = np.dot(np.dot(np.array(listaDiferencialTeste1).T, self.inversoCovariancia1), np.array(listaDiferencialTeste1))
                dist2 = np.dot(np.dot(np.array(listaDiferencialTeste2).T, self.inversoCovariancia2), np.array(listaDiferencialTeste2))
                dist3 = np.dot(np.dot(np.array(listaDiferencialTeste3).T, self.inversoCovariancia3), np.array(listaDiferencialTeste3))
                dist4 = np.dot(np.dot(np.array(listaDiferencialTeste4).T, self.inversoCovariancia4), np.array(listaDiferencialTeste4))
            
                menorDistanciaValor = sys.maxsize
                menorDistanciaId = None
                if dist1 < menorDistanciaValor :
                    menorDistanciaId = 1
                    menorDistanciaValor = dist1
                if dist2 < menorDistanciaValor :
                    menorDistanciaId = 2
                    menorDistanciaValor = dist2
                if dist3 < menorDistanciaValor :
                    menorDistanciaId = 3
                    menorDistanciaValor = dist3
                if dist4 < menorDistanciaValor :
                    menorDistanciaId = 4
                    menorDistanciaValor = dist4

                matrizConfusao[self.imagensTreinamento.index(pasta)][menorDistanciaId - 1] += 1
            
        acuracia = 0
        for i in range(0, 4):
            acuracia += matrizConfusao[i][i]

        fimExecucaoTreino = timer()

        self.matrizConfusao = ('''\n{}\t{}\t{}\t{}\n{}\t{}\t{}\t{}\n{}\t{}\t{}\t{}\n{}\t{}\t{}\t{}\n\nAcurácia: {} %\n\nEspecificidade: {}\n\nTempo de Execução: {} s\n'''.format(
                self.exibir2Digitos(matrizConfusao[0][0]), self.exibir2Digitos(matrizConfusao[0][1]), self.exibir2Digitos(matrizConfusao[0][2]), self.exibir2Digitos(matrizConfusao[0][3]),
                self.exibir2Digitos(matrizConfusao[1][0]), self.exibir2Digitos(matrizConfusao[1][1]), self.exibir2Digitos(matrizConfusao[1][2]), self.exibir2Digitos(matrizConfusao[1][3]),
                self.exibir2Digitos(matrizConfusao[2][0]), self.exibir2Digitos(matrizConfusao[2][1]), self.exibir2Digitos(matrizConfusao[2][2]), self.exibir2Digitos(matrizConfusao[2][3]),
                self.exibir2Digitos(matrizConfusao[3][0]), self.exibir2Digitos(matrizConfusao[3][1]), self.exibir2Digitos(matrizConfusao[3][2]), self.exibir2Digitos(matrizConfusao[3][3]),
                 "{:.2f}".format(acuracia), "{:.5f}".format((100 - acuracia)/300), "{:.2f}".format((fimExecucaoTreino - inicioExecucaoTreino)/100000))) 

        self.exibirMatrizConfusao()

    def exibir2Digitos(self, numero):
        if numero < 10: return '0' + str(numero)
        else: return numero

    def exibirMatrizConfusao(self):
        matrizConfusaoJanela = Toplevel(self.master) 
        matrizConfusaoJanela.title("Matriz de Confusão")
        matrizConfusaoJanela.geometry("300x300+408+250")
        Label(matrizConfusaoJanela, text =self.matrizConfusao).pack() 


    def exibirClassificacaoImagem(self, mensagem):
        matrizClassificacaoJanela = Toplevel(self.master) 
        matrizClassificacaoJanela.title("Classificação da Imagem")
        matrizClassificacaoJanela.geometry("300x300+408+250")
        Label(matrizClassificacaoJanela, text = mensagem).pack() 


    def classificarAreaInteresse(self):
        inicioExecucaoImagemSelecionada = timer()

        im = cv2.imread('./area_de_interesse.png', 0) # Instancia o cv2.imread da imagem selecionada
        data = np.array((im/8), 'int') # Divide os valores de cinza de im em 8 para que existam no máximo 32 tons de cinza
        g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32, normed=True, symmetric=True) # Calcula a matrix de co-ocorrência do nível de cinza da imagem.
                
        # Obtêm-se as características selecionadas pelo usuário
        if self.opcaoContraste:    
            contraste = greycoprops(g, 'contrast') # Calcula o contraste da matrix de co-ocorrência de níveis de cinza
            contraste = [sum(i) for i in contraste]
        if self.opcaoHomogeneidade:
            homogeneidade = greycoprops(g, 'homogeneity') # Calcula a homogeneidade da matrix de co-ocorrência de níveis de cinza
            homogeneidade = [sum(i) for i in homogeneidade]
        if self.opcaoEnergia:
            energia = greycoprops(g, 'energy') # Calcula a energia da matrix de co-ocorrência de níveis de cinza
            energia = [sum(i) for i in energia]
        if self.opcaoEntropia:
            entropia = shannon_entropy(data) # Calcula a entropia de Shannon da imagem
        if self.opcaoHu:
            hu = moments_hu(data) # Calcula os movimentos de Hu da imagem
            
        #self.caracteristicasImagensTeste[self.imagensTreinamento.index(pasta)][0]
        caracteristicasImagemSelect = np.concatenate((contraste, homogeneidade, energia, entropia, hu), axis=None)

        listaDiferencialTeste1 = np.subtract(caracteristicasImagemSelect, self.media1)
        listaDiferencialTeste2 = np.subtract(caracteristicasImagemSelect, self.media2)
        listaDiferencialTeste3 = np.subtract(caracteristicasImagemSelect, self.media3)
        listaDiferencialTeste4 = np.subtract(caracteristicasImagemSelect, self.media4)

        dist1 = np.dot(np.dot(np.array(listaDiferencialTeste1).T, self.inversoCovariancia1), np.array(listaDiferencialTeste1))
        dist2 = np.dot(np.dot(np.array(listaDiferencialTeste2).T, self.inversoCovariancia2), np.array(listaDiferencialTeste2))
        dist3 = np.dot(np.dot(np.array(listaDiferencialTeste3).T, self.inversoCovariancia3), np.array(listaDiferencialTeste3))
        dist4 = np.dot(np.dot(np.array(listaDiferencialTeste4).T, self.inversoCovariancia4), np.array(listaDiferencialTeste4))
        
        menorDistanciaValor = sys.maxsize
        menorDistanciaId = None
        if dist1 < menorDistanciaValor :
            menorDistanciaId = 1
            menorDistanciaValor = dist1
        if dist2 < menorDistanciaValor :
            menorDistanciaId = 2
            menorDistanciaValor = dist2
        if dist3 < menorDistanciaValor :
            menorDistanciaId = 3
            menorDistanciaValor = dist3
        if dist4 < menorDistanciaValor :
            menorDistanciaId = 4
            menorDistanciaValor = dist4

        fimExecucaoImagemSelecionada = timer()

        mensagem = ('''\nClasse BIRADS: {}\n\nTempo de Execução: {} s\n'''.format(
                menorDistanciaId, "{:.5f}".format((fimExecucaoImagemSelecionada - inicioExecucaoImagemSelecionada)/100000))) 

        self.exibirClassificacaoImagem(mensagem)

    def classificarImagem(self):
        inicioExecucaoImagemTotal = timer()

        im = cv2.imread(self.pathImagem, 0) # Instancia o cv2.imread da imagem selecionada
        data = np.array((im/8), 'int') # Divide os valores de cinza de im em 8 para que existam no máximo 32 tons de cinza
        g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32, normed=True, symmetric=True) # Calcula a matrix de co-ocorrência do nível de cinza da imagem.
                
        # Obtêm-se as características selecionadas pelo usuário
        if self.opcaoContraste:    
            contraste = greycoprops(g, 'contrast') # Calcula o contraste da matrix de co-ocorrência de níveis de cinza
            contraste = [sum(i) for i in contraste]
        if self.opcaoHomogeneidade:
            homogeneidade = greycoprops(g, 'homogeneity') # Calcula a homogeneidade da matrix de co-ocorrência de níveis de cinza
            homogeneidade = [sum(i) for i in homogeneidade]
        if self.opcaoEnergia:
            energia = greycoprops(g, 'energy') # Calcula a energia da matrix de co-ocorrência de níveis de cinza
            energia = [sum(i) for i in energia]
        if self.opcaoEntropia:
            entropia = shannon_entropy(data) # Calcula a entropia de Shannon da imagem
        if self.opcaoHu:
            hu = moments_hu(data) # Calcula os movimentos de Hu da imagem
            
        #self.caracteristicasImagensTeste[self.imagensTreinamento.index(pasta)][0]
        caracteristicasImagemSelect = np.concatenate((contraste, homogeneidade, energia, entropia, hu), axis=None)

        listaDiferencialTeste1 = np.subtract(caracteristicasImagemSelect, self.media1)
        listaDiferencialTeste2 = np.subtract(caracteristicasImagemSelect, self.media2)
        listaDiferencialTeste3 = np.subtract(caracteristicasImagemSelect, self.media3)
        listaDiferencialTeste4 = np.subtract(caracteristicasImagemSelect, self.media4)

        dist1 = np.dot(np.dot(np.array(listaDiferencialTeste1).T, self.inversoCovariancia1), np.array(listaDiferencialTeste1))
        dist2 = np.dot(np.dot(np.array(listaDiferencialTeste2).T, self.inversoCovariancia2), np.array(listaDiferencialTeste2))
        dist3 = np.dot(np.dot(np.array(listaDiferencialTeste3).T, self.inversoCovariancia3), np.array(listaDiferencialTeste3))
        dist4 = np.dot(np.dot(np.array(listaDiferencialTeste4).T, self.inversoCovariancia4), np.array(listaDiferencialTeste4))
        
        menorDistanciaValor = sys.maxsize
        menorDistanciaId = None
        if dist1 < menorDistanciaValor :
            menorDistanciaId = 1
            menorDistanciaValor = dist1
        if dist2 < menorDistanciaValor :
            menorDistanciaId = 2
            menorDistanciaValor = dist2
        if dist3 < menorDistanciaValor :
            menorDistanciaId = 3
            menorDistanciaValor = dist3
        if dist4 < menorDistanciaValor :
            menorDistanciaId = 4
            menorDistanciaValor = dist4

        fimExecucaoImagemTotal = timer()

        mensagem = ('''\nClasse BIRADS: {}\n\nTempo de Execução: {} s\n'''.format(
                menorDistanciaId, "{:.5f}".format((fimExecucaoImagemTotal - inicioExecucaoImagemTotal)/100000))) 

        self.exibirClassificacaoImagem(mensagem)

    # Contorna e recorta a área de interesse selecionada
    def selecionarAreaInteresse(self, event):
        if(self.areaSelecionada != None):
            self.canvas.delete(self.areaSelecionada)

        # coordenadas da janela em relação ao canvas
        coordCanvas = (self.canvas.canvasx(0),
                    self.canvas.canvasy(0))

        coordAncora = self.canvas.bbox(self.textoAncora) # coisa do lucca

        self.areaSelecionada = self.canvas.create_rectangle(
            event.x - (64 * self.imagemEscala) + coordCanvas[0],
            event.y - (64 * self.imagemEscala) + coordCanvas[1],
            event.x + (64 * self.imagemEscala) + coordCanvas[0], 
            event.y + (64 * self.imagemEscala) + coordCanvas[1],            
            outline="green")

        newImg = self.imagemModificada

        self.imagem.crop((
                    (event.x + coordCanvas[0] - coordAncora[0]) / self.imagemEscala - 64,
                    (event.y + coordCanvas[1] - coordAncora[1]) / self.imagemEscala - 64,
                    (event.x + coordCanvas[0] - coordAncora[0]) / self.imagemEscala + 64,
                    (event.y + coordCanvas[1] - coordAncora[1]) / self.imagemEscala + 64)).save('area_de_interesse.png')

    # Habilita a possibilidade de selecionar uma área de interesse
    def habilitarSelecaoAreaInteresse(self):
        if(self.areaSelecionada):
            self.canvas.delete(self.areaSelecionada)
        self.canvas.bind('<Button-3>', self.selecionarAreaInteresse) # Selecionar região de interesse 128x128

    # Lembra das coordenadas prévias à movimentação com o mouse
    def moverDe(self, event):
        self.coordClickOrigem = (event.x, event.y) # Define a coordenada do clique como a de origem
        self.canvas.scan_mark(event.x, event.y)

    # Arrasta o canvas para a nova posição
    def moverPara(self, event):
        # Registra a coordenada do ponteiro
        self.coordClickDestino = (event.x, event.y)
        # Arrasta todos os objetos do canvas junto com o ponteiro do mouse
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        # Calcula o delta da coordenata de origem e destino do clique
        diffx, diffy = (self.coordClickDestino[0] - self.coordClickOrigem[0],
                        self.coordClickDestino[1] - self.coordClickOrigem[1])

        # Incrementa o delta da movimentação do ponteiro à coordenada da imagem
        self.coordImagem = (self.coordImagem[0] + diffx, 
                            self.coordImagem[1] + diffy)

        # Menor valor de x que o pixel (0,0) pode assumir
        xMinImagem = 0 if \
                     self.imagem.size[0] * self.imagemEscala < self.master.winfo_width() \
                     else self.master.winfo_width() - self.imagem.size[0] * self.imagemEscala
        # Menor valor de y que o pixel (0,0) pode assumir
        yMinImagem = 0 if \
                     self.imagem.size[1] * self.imagemEscala < self.master.winfo_height() \
                     else self.master.winfo_height() - self.imagem.size[1] * self.imagemEscala
        # Maior valor de x que o pixel (0,0) pode assumir
        xMaxImagem = self.master.winfo_width() - self.imagem.size[0] * self.imagemEscala \
                     if self.master.winfo_width() > self.imagem.size[0] * self.imagemEscala \
                     else 0
        # Maior valor de y que o pixel (0,0) pode assumir
        yMaxImagem = self.master.winfo_height() - self.imagem.size[1] * self.imagemEscala \
                     if self.master.winfo_height() > self.imagem.size[1] * self.imagemEscala \
                     else 0

        novoX, novoY = self.coordImagem

        # Não permite a coordenada da imagem ser menor que 0 (o que corresponderia a sair da janela)
        if novoX < xMinImagem: novoX = xMinImagem
        if novoY < yMinImagem: novoY = yMinImagem
        if novoX > xMaxImagem: novoX = xMaxImagem
        if novoY > yMaxImagem: novoY = yMaxImagem
        
        self.coordImagem = (novoX, novoY)

        self.coordClickOrigem = self.coordClickDestino

    # Realiza o zoom na imagem com a roda do mouse
    def zoom(self, event):
        scale = 1.0

        # Responde ao evento de movimento da roda do mouse do Linux (event.num) ou Windows (event.delta)        
        if self.imagemEscala >= 0.05:
            if event.num == 5 or event.delta == -120:
                scale        *= self.delta
                self.imagemEscala *= self.delta
        
        if self.imagemEscala <= 10:
            if event.num == 4 or event.delta == 120:
                scale        /= self.delta
                self.imagemEscala /= self.delta

        # Redefine a escala de todos os objetos do canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.scale('all', x, y, scale, scale)
        self.mostrarImagem()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    # Vincula o clique de botões à ações
    def vincularBotoes(self):
        self.canvas.bind('<ButtonPress-1>', self.moverDe) # Botão esquerdo do mouse pressionado
        self.canvas.bind('<B1-Motion>', self.moverPara) # Mouse se movimentou com o botão esquerdo pressionado
        self.canvas.bind('<MouseWheel>', self.zoom)  # Uso do scroll do mouse (no Windows e MacOS, mas não no Linux)
        self.canvas.bind('<Button-5>', self.zoom)  # Uso do scroll do mouse para baixo (apenas no Linux)
        self.canvas.bind('<Button-4>', self.zoom)  # Uso do scroll do mouse para cima (apenas no Linux)

    # Implementa o menu com as opções listadas
    def criarMenu(self):
        menubar = Menu(self.master)
        
        opcoesClassificacao = Menu(menubar, tearoff=0)
        opcoesClassificacao.add_command(label="Importar imagem", command=self.abrirImagem)
        opcoesClassificacao.add_command(label="Selecionar região de interesse", command=self.habilitarSelecaoAreaInteresse)
        opcoesClassificacao.add_command(label="Classificar região de interesse", command=self.classificarAreaInteresse)
        opcoesClassificacao.add_command(label="Classificar imagem por inteiro", command=self.classificarImagem)
        menubar.add_cascade(label="Classificação", menu=opcoesClassificacao)
        
        checkCaracteristicas = Menu(menubar, tearoff=0)
        checkCaracteristicas.add_checkbutton(label='Entropia', variable=self.opcaoEntropia, onvalue=True, offvalue=False)
        checkCaracteristicas.add_checkbutton(label='Homogeneidade', variable=self.opcaoHomogeneidade, onvalue=True, offvalue=False)
        checkCaracteristicas.add_checkbutton(label='Energia', variable=self.opcaoEnergia, onvalue=True, offvalue=False)
        checkCaracteristicas.add_checkbutton(label='Contraste', variable=self.opcaoContraste, onvalue=True, offvalue=False)
        checkCaracteristicas.add_checkbutton(label='Momentos de Hu', variable=self.opcaoHu, onvalue=True, offvalue=False)

        opcoesTreinamento = Menu(menubar, tearoff=0)
        opcoesTreinamento.add_cascade(label='Selecionar Características', menu=checkCaracteristicas)
        opcoesTreinamento.add_command(label="Treinar classificação a partir do dataset", command=self.lerDiretorio)
        menubar.add_cascade(label="Treinamento", menu=opcoesTreinamento)

        self.master.config(menu=menubar)

    # Mostra a imagem no canvas
    def mostrarImagem(self):
        if self.imagemId:
            self.canvas.delete(self.imagemId)
            self.imageId = None
            self.canvas.imagetk = None  # Deleta a imagem prévia do canvas

        imagemLargura, imagemAltura = self.imagem.size
        novoTamanho = int(self.imagemEscala * imagemLargura), int(self.imagemEscala * imagemAltura)
        
        self.imagemModificada = self.imagem.resize(novoTamanho)
        imagetk = ImageTk.PhotoImage(self.imagemModificada)
        
        # Usa do objeto self.text para instanciar as coordinadas corretas
        self.imagemId = self.canvas.create_image(self.canvas.coords(self.textoAncora), anchor='nw', image=imagetk)
        
        #self.canvas.lower(self.imageid)  # set it into background
        self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

def main():
    root = Tk() # Instancia a janela principal
    
    app = Aplicacao(root, 'Agnitio')

    app.mainloop() # Chama o loop principal da instância de Tk

# Chama a função main
if __name__ == '__main__':
    main()
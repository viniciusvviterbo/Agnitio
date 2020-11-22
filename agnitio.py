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
import random

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
        self.janela_largura, self.janela_altura = self.getResolucaoTela() # Define as dimensões da janela
        
        self.canvas = None # Instancia da área de manipulação da imagem
        self.textoAncora = None # Define o texto que será usado como referência de instanciação da imagem
        self.imagemModificada = None # Instância do objeto manipulável que representa a imagem original
        self.coordImagem = None # Instancia das coordenadas da imagem
        self.coordClickOrigem = None
        self.coordClickDestino = None
        self.areaSelecionada = None # Define a area selecionada (quadrado verde)
        
        self.imagensTreinamento = None # Define o vetor que armazenará as imagens que serão utilizadas para treinamento

        self.opcaoEntropia = BooleanVar(value=False) # Define o valor das opções selecionadas na janela de seleção de características
        self.opcaoHomogeniedade = BooleanVar(value=False) # Define o valor das opções selecionadas na janela de seleção de características
        self.opcaoEnergia = BooleanVar(value=False) # Define o valor das opções selecionadas na janela de seleção de características
        self.opcaoContraste = BooleanVar(value=False) # Define o valor das opções selecionadas na janela de seleção de características
        self.opcaoHu =  BooleanVar(value=False) # Define o valor das opções selecionadas na janela de seleção de características

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
        # Lê o caminho do diretório escolhido pelo usuário
        caminhoDir = filedialog.askdirectory(title='Selecione o diretório de treinamento')
        # Garante que um diretório foi escolhido
        if type(caminhoDir) is str and caminhoDir != '':
            # Declara a lista de imagens (e dados relacionado) que serão utilizadas para treinamento
            # Cada tupla nesse array será composto como (CAMINHO_DA_IMG, NOME_IMG, PASTA_ORIGEM_IMG)
            self.imagensTreinamento = [[],[],[],[]]

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
        for pasta in self.imagensTreinamento: # Para cada array em self.imagensTreinamento
            random.shuffle(pasta) # Embaralha a ordem das tuplas nesse array
            for img in pasta: # Para cada tupla nesse array
                im = img[1] # Instancia o cv2.imread da imagem referenciada
                data = np.array((im/8), 'int') # Divide os valores de cinza de im em 8 para que existam no máximo 32 tons de cinza
                g = greycomatrix(data, [1, 2, 4, 8, 16], [0, np.pi/4, np.pi/2, 3*np.pi/4], levels=32, normed=True, symmetric=True) # Calcula a matrix de co-ocorrência do nível de cinza da imagem.
                
                constraste = None
                homogeniedade = None
                energia = None
                entropia = None
                hu = None

                if self.opcaoContraste:    
                    contraste = greycoprops(g, 'contrast') # Calcula o contraste da matrix de co-ocorrência de níveis de cinza
                if self.opcaoHomogeniedade:
                    homogeniedade = greycoprops(g, 'homogeneity') # Calcula a homogeniedade da matrix de co-ocorrência de níveis de cinza
                if self.opcaoEnergia:
                    energia = greycoprops(g, 'energy') # Calcula a energia da matrix de co-ocorrência de níveis de cinza
                if self.opcaoEntropia:
                    entropia = shannon_entropy(data) # Calcula a entropia de Shannon da imagem
                if self.opcaoHu:
                    hu = moments_hu(data) # Calcula os movimentos de Hu da imagem

                
                

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

        newImg.crop((
                    event.x - 64 + coordCanvas[0] - coordAncora[0],
                    event.y - 64 + coordCanvas[1] - coordAncora[1],
                    event.x + 64 + coordCanvas[0] - coordAncora[0],
                    event.y + 64 + coordCanvas[1] - coordAncora[1])).save('teste.png')

    # Habilita a possibilidade de selecionar uma área de interesse
    def habilitarSelecaoAreaInteresse(self):
        if(self.areaSelecionada):
            self.canvas.delete(self.areaSelecionada)
        self.canvas.bind('<Button-3>', self.selecionarAreaInteresse) # Selecionar região de interesse 128x128

    # Calcula as características da imagem ou da região de interesse selecionada
    def calcularCaracteristicas(self):
        print('Opção para calcular as características da imagem selecionada')

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
        menubar.add_cascade(label="Classificação", menu=opcoesClassificacao)
        
        checkCaracteristicas = Menu(menubar, tearoff=0)
        checkCaracteristicas.add_checkbutton(label='Entropia', variable=self.opcaoEntropia, onvalue=True, offvalue=False)
        checkCaracteristicas.add_checkbutton(label='Homogeniedade', variable=self.opcaoHomogeniedade, onvalue=True, offvalue=False)
        checkCaracteristicas.add_checkbutton(label='Energia', variable=self.opcaoEnergia, onvalue=True, offvalue=False)
        checkCaracteristicas.add_checkbutton(label='Contraste', variable=self.opcaoContraste, onvalue=True, offvalue=False)
        checkCaracteristicas.add_checkbutton(label='Momentos de Hu', variable=self.opcaoHu, onvalue=True, offvalue=False)

        opcoesTreinamento = Menu(menubar, tearoff=0)
        opcoesTreinamento.add_cascade(label='Selecionar Características', menu=checkCaracteristicas)
        opcoesTreinamento.add_command(label="Treinar classificação a partir do dataset", command=self.lerDiretorio)
        menubar.add_cascade(label="Treinamento", menu=opcoesTreinamento)




        '''
        opcoesArquivos = Menu(menubar, tearoff=0)
        opcoesArquivos.add_command(label="Sair", command=self.master.quit)
        menubar.add_cascade(label="Arquivos", menu=opcoesArquivos)

        opcoesManipulacao = Menu(menubar, tearoff=0)
        opcoesManipulacao.add_command(label="Treinar classificador", command=self.treinarClassificador)
        
        opcoesManipulacaoCaracteristicas = Menu(menubar, tearoff=0)
        opcoesManipulacaoCaracteristicas.add_command(label="Calcular características da imagem", command=self.calcularCaracteristicas)

        opcoesManipulacao.add_cascade(label="Características", menu=opcoesManipulacaoCaracteristicas)
        menubar.add_cascade(label="Manipulação", menu=opcoesManipulacao)
        '''

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
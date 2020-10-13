from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from PIL import ImageTk, Image
import os

class Aplicacao(Frame):
    def __init__(self, master=None, titulo=''):
        super().__init__(master)
        self.master = master
        # Define o título da imagem
        self.master.title(titulo)
        # Instancia a imagem da class como None
        self.imagemOriginal = None
        #Instancia da área da imagem
        self.canvas = None
        #Define a area selecionada
        self.areaSelecionada = None
        # Define as dimenções da janela
        tela_largura, tela_altura = self.getResolucaoTela()
        janela_largura = round(tela_largura/2)
        janela_altura = round(tela_altura/2)
        # Aplica as dimenções e posição da janela
        self.master.geometry(str(janela_largura) + 'x' + str(janela_altura) + '+' + str(round(tela_largura/4)) + '+' + str(round(tela_altura/4)))
        # Implementa o menu e seus componentes na janela
        self.criarMenu()

    def getResolucaoTela(self):
        # Obtêm as dimenções da tela
        tela_largura = self.master.winfo_screenwidth()
        tela_altura = self.master.winfo_screenheight()
        return (tela_largura, tela_altura)

    def getResolucaoJanela(self):
        janela_largura = self.master.winfo_width()
        janela_altura = self.master.winfo_height()
        return (janela_largura, janela_altura)

    def open_img(self):
        if(self.canvas!=None): 
            self.canvas.destroy()

        # Abre caixa de diálogo para seleção do arquivo
        fname = filedialog.askopenfilename(title='open')
        # Instancia a imagem selecionada
        self.imagemOriginal = Image.open(fname)
        # Redimensiona a imagem de acordo com as dimensões da janela em que está sendo exibida
        imagem_largura, imagem_altura = self.imagemOriginal.size
        janela_largura, janela_altura = self.getResolucaoJanela()

        if(imagem_largura > imagem_altura):
            imagem_altura = imagem_altura * (janela_largura / imagem_largura)
            imagem_largura = janela_largura
        else:
            imagem_largura = imagem_largura * (janela_altura / imagem_altura)
            imagem_altura = janela_altura

        img = self.imagemOriginal.resize((round(imagem_largura), round(imagem_altura)), Image.ANTIALIAS)

        # Inclui a imagem redimensionada na tela
        img = ImageTk.PhotoImage(img)
        canvas = Canvas(self.master, height=round(imagem_altura), width=round(imagem_largura))
        canvas.create_image(round(imagem_largura/2), round(imagem_altura/2), image=img)
        canvas.pack()
        canvas.image = img
        self.canvas = canvas

    def mouseBotaoEsquerdoPressionado(self, event):
        if(self.areaSelecionada != None):
            self.canvas.delete(self.areaSelecionada)
        self.areaSelecionada = self.canvas.create_rectangle(event.x-64, event.y-64, event.x+64, event.y+64, outline="red")
        newImg = self.imagemOriginal.resize((self.canvas.winfo_width(), self.canvas.winfo_height()), Image.ANTIALIAS)
        newImg.crop((event.x-64, event.y-64, event.x+64, event.y+64)).save('teste.png')

    def crop_img(self):
        if(self.areaSelecionada):
            self.canvas.delete(self.areaSelecionada)
        self.canvas.bind('<Button-1>', self.mouseBotaoEsquerdoPressionado)

    def criarMenu(self):
        menubar = Menu(self.master)
        
        opcaoMenu = Menu(menubar, tearoff=0)
        opcaoMenu.add_command(label="Importar imagem", command=self.open_img)
        opcaoMenu.add_command(label="Sair", command=self.master.quit)

        menubar.add_cascade(label="Arquivo", menu=opcaoMenu)

        menubar.add_command(label="Recortar", command=self.crop_img)

        self.master.config(menu=menubar)


def main():
    root = Tk() # Instancia a janela principal
    
    app = Aplicacao(root, 'Agnitio')

    app.mainloop() # Chama o loop principal da instância de Tk

# Chama a função main
if __name__ == '__main__':
    main()
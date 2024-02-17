from typing import List, Dict
from uuid import uuid4
from pymongo import MongoClient, errors
from pymongo.collection import Collection, IndexModel
#from src.config.config import env
from logging import INFO, WARNING, getLogger
from decimal import Decimal
import re
import os.path
import jsonpickle
from src.db.itens_database import Item

logger = getLogger('uvicorn')

class Carrinho():
    """Classe que representa um carrinho de um usuário
    
        Criar com método new_cart()

    Returns:
        (Cart, "SUCCESS"), ou (None, reason) caso o input não seja validado.
        
        reason será o nome do campo rejeitado pela validação
    """
    token: str
    items: dict[Item]

    def __init__(self, token: str):
        self.token = token
        self.items = dict()

    def new_cart(self, token: str):
        """Cria novo carrinho

        Args:
            token

        Returns:
            new cart object
        """
        cart = Carrinho(token)
        return cart
    
    def get_all_items(self):
        """Retorna todos os itens do carrinho"""
        return list(self.items.values())
    
    def add_new_item(self, item: Item):
        """Adicionar um novo item ao carrinho

        Args:
            item (Item): Item em questão
            
        Returns:
            success (bool): True para operação bem sucedida, False para mal sucedida
            reason (list[str]): contém "Item com mesmo ID já no carrinho" se for um item já existente.
            ["SUCCESS"] caso tenha sido uma operação bem sucedida
        """
        reason = []
        if self.get_item_by_ID(item.id):
            reason.append("Item com mesmo ID já no carrinho")
        
        if reason.__len__() > 0:
            return (False, reason)
        
        self.items[item.id] = item
        return (True, ["SUCCESS"])

    def remove_item_by_ID (self, item_id: int) -> Item | None:
        """ Remover um item do carrinho

        Args:
            item_id (int): ID do item em questão

        Returns:
            success (bool): True para operação bem sucedida, False para mal sucedida
            reason (list[str]): contém "NOT_FOUND" se o item não foi encontrado
            ["SUCCESS"] caso tenha sido uma operação bem sucedida
        """
        toreturn = self.items.pop(item_id, None)
        return toreturn

    def get_item_by_ID (self, item_id: int) -> Item | None:
        """ Acessar um item do carrinho

        Args:
            item_id (int): ID do item em questão

        Returns:
            Item (Item): Se o item for encontrado | None: Se o item não for encontrado.
        """
        for key,val in self.items.items():
            if val.id == item_id:
                return val
        return None
    
    def modify_item_by_ID (self, item_id: int, new_item: Item):
        """ Modificar um item da database

        Args:
            item_id (int): ID do item em questão
            new_item (Item): novos valores do item a ser modificado

        Returns:
            success (bool): True para operação bem sucedida, False para mal sucedida
            Item (Item | None): Se o item for encontrado.
        """
        reason = [] 
        if self.get_item_by_ID(item_id):
            reason.append("Item não encontrado")
            return(False, reason)
        
        self.items[item_id] = new_item
        return (True, ["SUCCESS"])


    def clear_database(self):
        self.items = dict()
        

class Carrinhos():
    db: dict[Carrinho]
    file_path:str

    def __init__(self, path: str = "Carrinhos.json"):
        self.db = dict()
        self.file_path = path
        self.try_read_from_file()

    def try_read_from_file(self):
        # Ler itens do arquivo
        if not os.path.exists(self.file_path):
            self.write_to_file()
            return None

        with open(self.file_path) as file:
            carrinhos = file.read()
            db = jsonpickle.decode(carrinhos)
            if type(db) == dict:
                self.db = db
    
    def write_to_file(self):
        objetos = jsonpickle.encode(self.db)
        with open(self.file_path, 'w+') as file:
            file.write(objetos)
    
    def get_cart_list(self, update = True):
        """Retorna todos os carrinhos da database"""
        if update:
            self.try_read_from_file()
        return list(self.db.values())
    
    def add_new_cart(self, carrinho: Carrinho, update: bool = True):
        """Adicionar um novo carrinho a database

        Args:
            carrinho (Carrinho): Carrinho em questão
            
        Returns:
            success (bool): True para operação bem sucedida, False para mal sucedida
            reason (list[str]): contém "Carrinho com mesmo token já na base de dados" se for um token já existente.
            ["SUCCESS"] caso tenha sido uma operação bem sucedida
        """
        reason = []
        if update:
            self.try_read_from_file()
        if self.get_cart_by_token(carrinho.token, False):
            reason.append("Carrinho com mesmo token já na base de dados")
        
        if reason.__len__() > 0:
            return (False, reason)
        
        self.db[carrinho.token] = carrinho
        self.write_to_file()
        return (True, ["SUCCESS"])

    def remove_cart_by_token (self, token: str, update: bool = True) -> Item | None:
        """ Remover um carrinho da database

        Args:
            token (str): token do carrinho em questão

        Returns:
            carrinho (Carrinho | None): carrinho removido ou None.
        """
        if update:
            self.try_read_from_file()
        toreturn = self.db.pop(token, None)
        self.write_to_file()
        return toreturn

    def get_cart_by_token (self, token: str, update: bool = True) -> Item | None:
        """ Acessar um item da database

        Args:
            token (str): token do carrinho em questão

        Returns:
            success (bool): True para operação bem sucedida, False para mal sucedida
            Carrinho (Carrinho | None): Se o carrinho for encontrado.
        """
        if update:
            self.try_read_from_file
        for key,val in self.db.items():
            if val.token == token:
                return val
        return None
    
    def modify_item_all_carts (self, item_id: int, new_item: Item, update: bool = True):
        """ Modificação em um item da database (chamar para aplicar alteração em todos os carrinhos que apresentam o item)

        Args:
            item_id (int): ID do item em questão
            new_item (Item): novos valores do item a ser modificado

        Returns:
            
        """
        if update:
            self.try_read_from_file()
        
        for token, cart in self.db:
            for id, item in cart:
                if id == item_id:
                    cart[id] = new_item

        self.write_to_file()


    def remove_item_all_carts(self, item_id: int, update: bool = True):
        """Remove um item especificado por item_id de todos os carrinhos na base de dados (chamar para aplicar alteração em todos os carrinhos que apresentam o item).

        Args:
            item_id (int): ID do item a ser removido.
            update (bool): Se True, atualiza a base de dados a partir do arquivo JSON antes da operação.

        """
        if update:
            self.try_read_from_file()

        for cart_token, cart in self.db.items():
            if item_id in cart.items:
                del cart.items[item_id]

        self.write_to_file()

    def clear_cart_database(self):
        self.db = dict()
        self.write_to_file()

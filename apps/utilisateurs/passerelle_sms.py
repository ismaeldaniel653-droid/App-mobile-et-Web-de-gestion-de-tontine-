from abc import ABC, abstractmethod


class PasserelleSms(ABC):
    @abstractmethod
    def envoyer_code(self, telephone, code):
        raise NotImplementedError


class PasserelleSmsConsole(PasserelleSms):
    def envoyer_code(self, telephone, code):
        telephone_masque = f"{telephone[:4]}***{telephone[-2:]}"
        print(f"Code de connexion pour {telephone_masque} : {code}")
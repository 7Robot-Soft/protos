#!/usr/bin/env python
#-*- coding: utf-8 -*-

from struct import pack, unpack

class Packet:
    pass

class MPacket:
    """Créé un objet Packet custom"""
    def __init__(self, id, attrs):
        self.id = id
        self.attrs = attrs
        self.format = ""
        for c in attrs:
            self.format += c[1]
        
    def pack(self, *buff):
        return pack("I", self.id) + pack(self.format, *buff)
            
        
    def unpack(self, buff):
        # code factorisé dans la classe mère
        format = "I"+"".join(self.format)
        decoded =  unpack(format, buff)
        p = Packet()
        p.id = decoded[0] # + no de carte
        for i in range(len(self.attrs)):
            p.__setattr__(self.attrs[i][0], decoded[i+1])
        return p
        
    
class Factory:
    """Générateur"""
    @staticmethod
    def init(classe):
        # Optimisation
        # génère msgs = [dist, stop, pos]
        # en statique comme ça c'est calculé une fois pour toutes
        classe.packets = {}
        for attrn in classe.__dict__:
            attr = classe.__getattribute__(classe, attrn)
            if isinstance(attr, MPacket):
                classe.packets[attrn] = attr
                
        classe.pack   = lambda name, *buff:   classe.packets[name].pack(*buff)
        classe.unpack = lambda name, *buff:   classe.packets[name].unpack(*buff)
        

class Champ:
    def __init__(self, nom, ctype):
        self.nom = nom
        self.ctype = ctype

class CStruct:
    def __init__(self, id, nom):
        self.id = id
        self.nom = nom
        self.champs = []
        self.size = 0
    def ajoute_champ(self, nom, ctype):
        self.champs.append(Champ(nom,  ctype))
        self.size += ctype[1]
        
    def __str__(self):
        res = "typedef %s struct %s_ {" % (self.nom.capitalize(), self.nom)
        for champ in self.champs:
            res +=  "\n\t %s %s;" % (champ.ctype[0],champ.nom)
            #~ ctype = CGenerator.type_converter(champ[1])
            #~ print ("\t", ctype[0],champ[0], ";")
            #~ fields.append((ctype[1],ctype[0],champ[0]))
        res += "\n};"
        return res
                    
class CGenerator:
    """Générateur de code C"""
    
    # TODO define pour type
    
    @staticmethod
    def generate(classe):
        for nom_attribut in classe.__dict__:
            attribut = getattr(Asserv, nom_attribut)
            if isinstance(attribut, MPacket):
                fields = CGenerator.gen_struct(nom_attribut, attribut)
                print (fields.__str__())
                CGenerator.gen_conversion(nom_attribut, fields.size)
    
    @staticmethod
    def gen_struct(nom, packet):
        cstruct = CStruct(packet.id, nom)
        for champ in packet.attrs:
            ctype = CGenerator.type_converter(champ[1])
            cstruct.ajoute_champ(champ[0], ctype)
        return cstruct
        
    def gen_conversion(nom, size):
        #FIXME : prévoir la taille du header
        print ("char* pack_%s(%s* %s) {" % (nom, nom.capitalize(), nom))
        print ("\tchar* buffer = (char*)malloc(%d);" % size)
        print("\tmemcpy(buffer, (char*)%s, %s);" % (nom, size))
        print("}")
        
        print("void unpack_%s(char* buffer, int size, %s* %s) {" % (nom, nom.capitalize(), nom))
        print("\tmemcpy((char*)%s, buffer, %s);" % (nom, size))
        print("}")

            
    def type_converter(nom_type):
        """Ranvoie le type C et sa taille, gère les tableaux"""
        i = 0
        while i<len(nom_type) and nom_type[i].isdigit():
            i += 1
        ctype = CGenerator.simple_type_converter(nom_type[i:])
        if i==0:
            return ctype
        else:
            if ctype[0].find("char") != -1:
                i += 1
            return (ctype[0]+"["+str(i)+"]", i*ctype[1])
            
    def simple_type_converter(nom_type):
        """Ranvoie le type C et sa taille"""
        if nom_type == "c":
            return ("char", 1)
        elif nom_type == "b":
            return ("signed char", 1)
        elif nom_type == "B":
            return ("unsigned char", 1)
        elif nom_type == "f":
            return ("float", 4)
        elif nom_type == "h":
            return ("short", 2)
        elif nom_type == "H":
            return ("unsigned short", 2)
        elif nom_type == "I":
            return ("unsigned int", 4)
        elif nom_type == "i":    
            return ("int", 4)
        elif nom_type == "l":    
            return ("long", 8)
        elif nom_type == "L":    
            return ("unsigned long", 8)
        elif nom_type == "q":    
            return ("long long", 16)
        elif nom_type == "Q":    
            return ("unsigned long long", 16)
        elif nom_type == "d":    
            return ("double", 8)
        elif nom_type == "s":    
            return ("char*", 4)
        elif nom_type == "P":    
            return ("void*", 4)
        
        else:
            return ("void*", 4)
        

# --------------------------------
# ON définit ici la sémantique de notre protocole        
              
class Asserv:
    type    = 1
    dist    = MPacket(1, [
                          ("dist", "I"),
                         ])
    stop    = MPacket(2, [])
    pos     = MPacket(3, [
                          ("x", "f"),
                          ("y", "f"),
                        ])
          

# --------------------------------
# Tests  
        
Factory.init(Asserv)  # Mise en cache/création des mathodes pack/unpack et des attributs format et packets


binmsg = Asserv.pack("pos", 7,8)       # Sérialise
objmsg = Asserv.unpack("pos", binmsg)  # Créé une instance de Packet
print (objmsg.x, objmsg.y)             # ainsi on accède aux champs par attribut

CGenerator.generate(Asserv)

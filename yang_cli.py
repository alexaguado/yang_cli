#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import prompt

import json, sys, os

def fill_config(path, config, type):
    steps=path.split("/")[:-1]
    final=path.split("/")[-1]
    aux=config
    for s in steps:
        if s in aux.keys(): aux=aux[s]
        else:
            aux[s]={}
            aux=aux[s]
    if final not in aux.keys():
        if type == "leaf-list":
            aux[final]=[]
        if type == "leaf":
            aux[final]=None
        else:
            aux[final]={}

def fill_data(path, config, content):
    steps=path.split("/")[:-1]
    final=path.split("/")[-1]
    aux=config
    for s in steps:
        if s in aux.keys(): aux=aux[s]
        else:
            aux[s]={}
            aux=aux[s]
    aux[final]=content

def fill_value(path, config, type, value):
    steps=path.split("/")[:-1]
    final=path.split("/")[-1]
    aux=config
    for s in steps:
        aux=aux[s]
    if type=="leaf": aux[final]=value
    elif type=="leaf-list":
        if len(aux[final])==0:
            aux[final] = list()
        aux[final].append(value)
    else: aux[final].append(value)


def delete_info(cp,config):
    steps=cp.split("/")[:-1]
    final=cp.split("/")[-1]
    aux=config
    for s in steps:
        if s in aux.keys(): aux=aux[s]
        else:
            aux[s]={}
            aux=aux[s]
    del aux[final]

def find_json(path,config):
    steps=path.split("/")
    aux=config
    for s in steps:
        aux=aux[s]
    return aux

def load_choices(path,data,el,build):
    ret=""
    for c in data[path]["children"]:
        if data[path+"/"+c]["type"] in ["case","choice"]:
            if path+"/"+c+"/"+el in data.keys() and data[path+"/"+c+"/"+el]["type"] not in ["case","choice"]: return build+"/"+c
            else: ret+=load_choices(path+"/"+c,data,el,build+"/"+c)
    return ret

def load_rc(cp,mp,js,data,isfirst):
    ret={}
    err=False
    choices=""
    if mp not in data.keys():
        parent='/'.join(mp.split("/")[:-1])
        el=mp.split("/")[-1]
        choices=load_choices(parent,data,el,"")[1:]
        if len(choices)!=0:
            steps=choices.split("/")
            mp=parent+"/"+choices+"/"+el
            cp="/".join(cp.split("/")[:-1])+"/"+choices+"/"+el
    if err:
        print "Error loading: "+mp
    else:
        ctype=data[mp]["type"]
        if ctype=="leaf":
            return choices,js
        elif ctype=="leaf-list":
            return choices,js
        elif isinstance(js,dict):
            for k in js.keys():
                kaux=k.split(":")[-1]
                if isfirst:
                    ext,info=load_rc(kaux,kaux,js[k],data,False)
                    if len(ext)!=0: kaux=ext+"/"+kaux
                    fill_data(kaux,ret,info)
                else:
                    ext,info=load_rc(cp+"/"+kaux,mp+"/"+kaux,js[k],data,False)
                    if len(ext)!=0: kaux=ext+"/"+kaux
                    fill_data(kaux,ret,info)
        else:
            if isfirst: print "ERROR"
            for k in js:
                keyname=data[mp]["key"]
                mkaux=keyname.split(" ")
                key=""
                for w in mkaux:
                    key+=k[w]+","
                ret[key[:-1]]=load_rc(cp+"/"+key,mp,k,data,False)[1]
        return choices, ret

def ret_nochoice_keys(path,js,data,skip):
    ret=[]
    st=skip
    for k in js.keys():
        if data[path+"/"+k]["type"] in ("choice","case"):
            auxret=ret_nochoice_keys(path+"/"+k,js[k],data,skip+"/"+k)
            ret+=auxret
        else: ret.append(skip+"/"+k)
    return ret

def from_dict_to_rc(path,cnt,js,pprefix,isfirst):
    ret=None
    ctype=cnt[path]["type"]
    if ctype=="list":
        ret=[]
        if isfirst:
            auxret={}
            for k in js.keys():
                nwpath=path+"/"+k
                if cnt[nwpath]["type"] in ("choice","case"):
                    elems = ret_nochoice_keys(nwpath,js[k],cnt,k)
                    for el in elems:
                        e=el.split("/")[-1]
                        nwpath=path+"/"+el
                        pfx=cnt[nwpath]["orig"]
                        add=""
                        spfx=pprefix
                        if pprefix!=pfx:
                            add=pfx+":"
                            spfx=pfx
                        next=js
                        for l in el.split("/"):
                            next=next[l]
                        auxret[add+e]=from_dict_to_rc(nwpath,cnt,next,spfx,False)
                else:
                    pfx=cnt[nwpath]["orig"]
                    add=""
                    spfx=pprefix
                    if pprefix!=pfx:
                        add=pfx+":"
                        spfx=pfx
                    auxret[add+k]=from_dict_to_rc(nwpath,cnt,js[k],spfx,False)
            ret.append(auxret)
        else:
            for j in js.keys():
                auxret={}
                for k in js[j].keys():
                    nwpath=path+"/"+k
                    if cnt[nwpath]["type"] in ("choice","case"):
                        elems = ret_nochoice_keys(nwpath,js[j][k],cnt,k)
                        for el in elems:
                            e=el.split("/")[-1]
                            nwpath=path+"/"+el
                            pfx=cnt[nwpath]["orig"]
                            add=""
                            spfx=pprefix
                            if pprefix!=pfx:
                                add=pfx+":"
                                spfx=pfx
                            next=js[j]
                            for l in el.split("/"):
                                next=next[l]
                            auxret[add+e]=from_dict_to_rc(nwpath,cnt,next,spfx,False)
                    else:
                        pfx=cnt[nwpath]["orig"]
                        add=""
                        spfx=pprefix
                        if pprefix!=pfx:
                            add=pfx+":"
                            spfx=pfx
                        auxret[add+k]=from_dict_to_rc(nwpath,cnt,js[j][k],spfx,False)
                ret.append(auxret)
    elif ctype in ("leaf","leaf-list"): ret=js
    else:
        ret={}
        for k in js.keys():
            nwpath=path+"/"+k
            if cnt[nwpath]["type"] in ("choice","case"):
                elems = ret_nochoice_keys(nwpath,js[k],cnt,k)
                for el in elems:
                    e=el.split("/")[-1]
                    nwpath=path+"/"+el
                    pfx=cnt[nwpath]["orig"]
                    add=""
                    spfx=pprefix
                    if pprefix!=pfx:
                        add=pfx+":"
                        spfx=pfx
                    next=js
                    for l in el.split("/"):
                        next=next[l]
                    ret[add+e]=from_dict_to_rc(nwpath,cnt,next,spfx,False)
            else:
                pfx=cnt[nwpath]["orig"]
                add=""
                spfx=pprefix
                if pprefix!=pfx:
                    add=pfx+":"
                    spfx=pfx
                ret[add+k]=from_dict_to_rc(nwpath,cnt,js[k],spfx,False)
    return ret

def build_url(cfgp, curp, cnt, cfg):
    elms=cfgp.split("/")
    url="/restconf/data"
    pprefix=""
    auxpth=""
    for el in elms:
        if el in curp:
            auxpth+=el+"/"
            preamble=""
            pfx=cnt[auxpth[:-1]]['orig']
            if pfx!=pprefix:
                preamble=pfx+":"
                pprefix=pfx
            url+="/"+preamble+el
        else: url+="="+el
    return url

def restconf(cfgp, curp, cnt, cfg, session):
    if cnt[curp]["type"]=="list" and cfgp.split("/")[-1]==curp.split("/")[-1]:
        print "This operation is not supported at this level."
    else:
        completer = WordCompleter(["GET","POST","PUT","PATCH","DELETE","back"], ignore_case=True)
        text = session.prompt('select method> ',completer=completer,complete_while_typing=False)
        if text=="GET":
            print "\nExample request:\n"
            print "\tGET "+build_url(cfgp, curp, cnt, cfg)+" HTTP/1.1"
            print "\tHost: example.com"
            print "\tAccept: application/yang-data+json\n"
        elif text=="POST":
            auxurl=build_url(cfgp, curp, cnt, cfg)
            pprefix=cnt[curp]["orig"]
            url='/'.join(auxurl.split("/")[:-1])
            node=auxurl.split("/")[-1].split("=")[0]
            print "\nExample request:\n"
            print "\tPOST "+url+" HTTP/1.1"
            print "\tHost: example.com"
            print "\tAccept: application/yang-data+json\n"
            print(json.dumps({pprefix+":"+node:from_dict_to_rc(curp,cnt,find_json(cfgp,cfg),pprefix, True)}, indent=4, sort_keys=True)+"\n")
            #else: print(json.dumps({pprefix+":"+node:find_json(cfgp,cfg)}, indent=4, sort_keys=True)+"\n")
        elif text=="PUT":
            auxurl=build_url(cfgp, curp, cnt, cfg)
            pprefix=cnt[curp]["orig"]
            node=auxurl.split("/")[-1].split("=")[0]
            print "\nExample request:\n"
            print "\tPUT "+auxurl+" HTTP/1.1"
            print "\tHost: example.com"
            print "\tAccept: application/yang-data+json\n"
            print(json.dumps({pprefix+":"+node:from_dict_to_rc(curp,cnt,find_json(cfgp,cfg),pprefix, True)}, indent=4, sort_keys=True)+"\n")
        elif text=="PATCH":
            auxurl=build_url(cfgp, curp, cnt, cfg)
            pprefix=cnt[curp]["orig"]
            node=auxurl.split("/")[-1].split("=")[0]
            print "\nExample request:\n"
            print "\tPATCH "+auxurl+" HTTP/1.1"
            print "\tHost: example.com"
            print "\tAccept: application/yang-data+json\n"
            print(json.dumps({pprefix+":"+node:from_dict_to_rc(curp,cnt,find_json(cfgp,cfg),pprefix, True)}, indent=4, sort_keys=True)+"\n")
        elif text=="DELETE":
            print "\nExample request:\n"
            print "\tDELETE "+build_url(cfgp, curp, cnt, cfg)+" HTTP/1.1"
            print "\tHost: example.com"
            print "\tAccept: application/yang-data+json\n"
        else:
            print "Method not supported."

def get_existing_keys(path,config):
    steps=path.split("/")
    aux=config
    try:
        for s in steps:
            aux=aux[s]
        return aux.keys()
    except:
        return []

def prompt_pyang(content):

    aux=sorted(content.keys())

    roots=[]

    for i in aux:
        if "/" not in i:
            roots.append(i)

    cmds=["save","saverc","load","loadrc","show-config","rc","delete","pwd","back","exit","logout","?"]

    our_history = FileHistory('.pynavigate-history-file')

    session = PromptSession(history=our_history)

    config={}
    configpath=""

    meta={}
    for r in roots:
        meta[r]=content[r]["desc"]

    current=""
    stay=True
    completer = WordCompleter(roots+cmds, meta_dict=meta, ignore_case=True)

    amiinconfigurable=False

    ctype=None

    while stay:
        txt="yang-cli> "
        # If you do not want to update the path, delete the next two lines.
        if len(configpath)!=0 and len(configpath)<=50: txt=configpath+"> "
        elif len(configpath)!=0: txt="..."+configpath[-50:]+"> "
        text = session.prompt(txt,completer=completer,complete_while_typing=False)
        # print('%s' % text)
        # print('%s' % current)
        if text=="exit" or text=="logout":
            stay=False
        elif text=="pwd":
            print configpath
        elif text=="show-config":
            print(json.dumps(config, indent=4, sort_keys=True))
        elif text=="save":
            ins=raw_input("file: ")
            cfile=open(ins,"w")
            cfile.write(json.dumps(config, indent=4, sort_keys=True))
        elif text=="saverc":
            ins=raw_input("file: ")
            cfile=open(ins,"w")
            write=True
            if len(config.keys())>=1:
                completer = WordCompleter(config.keys(), ignore_case=True)
                print "Multiple roots"
                text = session.prompt('select root> ',completer=completer,complete_while_typing=False)
                if text not in config.keys():
                    print "No valid root selected"
                    write=False
                else:
                    k=text
            else: k=config.keys()[0]
            if write:
                cfgrc=from_dict_to_rc(k,content,config[k],content[k]["orig"],True)
                cfile.write(json.dumps({content[k]["orig"]+":"+k:cfgrc}, indent=4, sort_keys=True))
        elif text=="loadrc":
            files=[]
            for (dirpath, dirnames, filenames) in os.walk("."):
                for f in filenames:
                    if os.path.isfile(dirpath+"/"+f):
                        if dirpath==".": files.append(f)
                        else: files.append(dirpath+"/"+f)
            auxcomp=completer
            completer = WordCompleter(files, ignore_case=True)
            ins = session.prompt('file> ',completer=completer,complete_while_typing=False)
            completer=auxcomp
            #ins=raw_input("file: ")
            if os.path.isfile(ins):
                with open(ins,"r") as file:
                    #try:
                    cfgaux=json.loads(file.read())
                    auxlst=[]
                    auxcfg={}
                    if len(cfgaux.keys())>1:
                        print "Non-valid json. Multiple roots."
                    else:
                        r=cfgaux.keys()[0]
                        auxcfg.update(load_rc(r.split(":")[-1],r.split(":")[-1],cfgaux,content,True)[1])
                        config=auxcfg
                    #except:
                    #    print "Malformed json"
            else:
                print "File not found"
        elif text=="load":
            files=[]
            for (dirpath, dirnames, filenames) in os.walk("."):
                for f in filenames:
                    if os.path.isfile(dirpath+"/"+f):
                        if dirpath==".": files.append(f)
                        else: files.append(dirpath+"/"+f)
            auxcomp=completer
            completer = WordCompleter(files, ignore_case=True)
            ins = session.prompt('file> ',completer=completer,complete_while_typing=False)
            completer=auxcomp
            if os.path.isfile(ins):
                with open(ins,"r") as file:
                    try:
                        config=json.loads(file.read())
                    except:
                        print "Malformed json"
            else:
                print "File not found"
        elif text=="rc" and len(current)!=0:
            restconf(configpath,current,content,config,session)
        elif text=="delete":
            if current=="":
                print "You cannot delete the root!"
            else:
                delete_info(configpath,config)
                ctype=None
                if current in roots:
                    current=""
                    configpath=""
                    completer = WordCompleter(roots, ignore_case=True)
                else:
                    if configpath.split("/")[-1] in current:
                        current='/'.join(current.split("/")[:-1])
                        configpath='/'.join(configpath.split("/")[:-1])
                        meta={}
                        for ch in content[current]["children"]:
                            meta[ch]=content[current+"/"+ch]["desc"]
                        completer = WordCompleter(content[current]["children"]+cmds, meta_dict=meta, ignore_case=True)
                        amiinconfigurable=False
                    else:
                        configpath='/'.join(configpath.split("/")[:-1])
                        extra=get_existing_keys(configpath,config)
                        if len(content[current]["key"].split(" "))==1:
                            meta["<"+content[current]["key"]+">"]=content[current+"/"+content[current]["key"]]["desc"]
                        completer = WordCompleter(["<"+content[current]["key"].replace(" ", ",")+">"]+extra+cmds, meta_dict=meta, ignore_case=True)
                        amiinconfigurable=True
        elif text=="back":
            ctype=None
            if current in roots:
                current=""
                configpath=""
                completer = WordCompleter(roots, ignore_case=True)
            elif current=="":
                print "I am (g)root"
            else:
                if configpath.split("/")[-1] in current:
                    current='/'.join(current.split("/")[:-1])
                    configpath='/'.join(configpath.split("/")[:-1])
                    meta={}
                    for ch in content[current]["children"]:
                        meta[ch]=content[current+"/"+ch]["desc"]
                    completer = WordCompleter(content[current]["children"]+cmds, meta_dict=meta, ignore_case=True)
                    amiinconfigurable=False
                else:
                    configpath='/'.join(configpath.split("/")[:-1])
                    extra=get_existing_keys(configpath,config)
                    if len(content[current]["key"].split(" "))==1:
                        meta["<"+content[current]["key"]+">"]=content[current+"/"+content[current]["key"]]["desc"]
                    completer = WordCompleter(["<"+content[current]["key"].replace(" ", ",")+">"]+extra+cmds, meta_dict=meta, ignore_case=True)
                    amiinconfigurable=True
        elif text=="?" and len(current)!=0:
            if "desc" in content[current].keys(): print content[current]["desc"]
        elif ctype:
            fill_value(configpath,config,content[current]["type"], text)
        elif " " in text and not amiinconfigurable: #Verify for the tricky situations
            text=text.replace(" ","/")
            if not (len(current)!=0 and current+"/"+text not in content.keys()) and not (len(current)==0 and text not in content.keys()):
                if len(current)==0:
                    current=text
                    configpath=text
                else:
                    current=current+"/"+text
                    configpath=configpath+"/"+text
                if "children" in content[current].keys():
                    meta={}
                    if content[current]["key"] and not amiinconfigurable:
                        meta["<"+content[current]["key"]+">"]=content[current+"/"+content[current]["key"]]["desc"]
                        extra=get_existing_keys(configpath,config)
                        completer = WordCompleter(["<"+content[current]["key"]+">"]+extra+cmds, meta_dict=meta, ignore_case=True)
                        amiinconfigurable=True
                        fill_config(configpath,config,content[current]["type"])
                    else:
                        children=[]
                        for ch in content[current]["children"]:
                            if current+"/"+ch in content.keys():
                                meta[ch]=content[current+"/"+ch]["desc"]
                                children.append(ch)
                        completer = WordCompleter(children+cmds, meta_dict=meta, ignore_case=True)
                        amiinconfigurable=False
                        fill_config(configpath,config,content[current]["type"])
                else: completer = WordCompleter(cmds, ignore_case=True)
        elif len(text)==0: pass
        elif not amiinconfigurable and ((len(current)!=0 and current+"/"+text not in content.keys()) or (len(current)==0 and text not in content.keys())):
            print("Invalid command")
        else:
            if amiinconfigurable:
                nkeys=len(content[current]["key"].split())
                nentries=len(text.split(","))
                if nkeys!=nentries:
                    print "You have not entered the right number of keys!!!"
                    continue
                if len(configpath)==0:
                    configpath=text
                else:
                    configpath=configpath+"/"+text
            else:
                if len(current)==0:
                    current=text
                    configpath=text
                else:
                    current=current+"/"+text
                    configpath=configpath+"/"+text
            if "children" in content[current].keys():
                meta={}
                if content[current]["key"] and not amiinconfigurable:
                    #TODO: Double check this multi-key corner case
                    if len(content[current]["key"].split(" "))==1:
                        meta["<"+content[current]["key"]+">"]=content[current+"/"+content[current]["key"]]["desc"]
                    extra=get_existing_keys(configpath,config)
                    completer = WordCompleter(["<"+content[current]["key"].replace(" ", ",")+">"]+extra+cmds, meta_dict=meta, ignore_case=True)
                    amiinconfigurable=True
                    fill_config(configpath,config,content[current]["type"])
                else:
                    children=[]
                    for ch in content[current]["children"]:
                        if current+"/"+ch in content.keys():
                            meta[ch]=content[current+"/"+ch]["desc"]
                            children.append(ch)
                    completer = WordCompleter(children+cmds, meta_dict=meta, ignore_case=True)
                    amiinconfigurable=False
                    fill_config(configpath,config,content[current]["type"])
            else:
                completer = WordCompleter(["<"+content[current]["itype"]+">"]+cmds, ignore_case=True)
                fill_config(configpath,config,content[current]["type"])
                ctype=content[current]["type"]

with open(sys.argv[1],"r") as file:
    trash=json.loads(file.read())

content=trash

for key in trash.keys():
    if trash[key]["config"]:
        content[key]=trash[key]

prompt_pyang(content)

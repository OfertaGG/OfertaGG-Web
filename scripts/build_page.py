#!/usr/bin/env python3
"""Junta src/shell.html + src/style.css + src/app.js en site/index.html.
Solo hace falta ejecutarlo si cambias el diseño (no los precios)."""
import os
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd=lambda p:open(os.path.join(R,p),encoding="utf-8").read()
body=rd("src/shell.html").replace("/*CSS*/",rd("src/style.css")).replace("/*APP*/",rd("src/app.js"))
i=body.index('<div class="demo"')
head=('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
 '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
 '<style>[hidden]{display:none!important}body{margin:0}img{max-width:100%}</style>\n')
open(os.path.join(R,"site/index.html"),"w",encoding="utf-8").write(head+body[:i]+"</head>\n<body>\n"+body[i:]+"\n</body>\n</html>\n")
# versión para la vista previa en Claude (sin cabecera, la añade la plataforma)
open(os.path.join(R,"preview.html"),"w",encoding="utf-8").write(body)
print("site/index.html listo")

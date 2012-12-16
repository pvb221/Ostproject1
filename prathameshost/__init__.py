from flask import Flask
import settings
app = Flask('prathameshost')
app.config.from_object('prathameshost.settings')

import views

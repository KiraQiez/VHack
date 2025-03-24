import google.generativeai as genai

genai.configure(api_key="AIzaSyCCMqub_m4O8umGE_Rw_iuGIDkxPBl7QKE")

models = genai.list_models()
for model in models:
    print(model.name)

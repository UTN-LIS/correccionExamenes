import sys
sys.path.append('.')
from cliente_llm import ClienteLLM

print("Initializing ClienteLLM...")
client = ClienteLLM()
print(f"URL: {client.url}")

print("Sending test message...")
resp, t = client.generar_salida("Eres un robot que responde 'Hola'", "Di algo")
print(f"Response: {resp}")
print(f"Time: {t} seconds")

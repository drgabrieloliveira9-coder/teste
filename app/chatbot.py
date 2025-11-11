from flask import Blueprint, request, jsonify, render_template
import os
import re

chatbot = Blueprint('chatbot', __name__)

try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
    else:
        model = None
except ImportError:
    model = None

def get_simple_response(message):
    from app.db_operations import Product, Settings
    
    message_lower = message.lower()
    
    settings = Settings.get()
    store_info = dict(settings) if settings else {}
    store_name = store_info.get('store_name', 'Meatz Burger')
    phone = store_info.get('phone', '(11) 99999-9999')
    address = store_info.get('address', 'Rua Exemplo, 123')
    hours = store_info.get('opening_hours', 'Seg-Dom: 11h-23h')
    
    if any(word in message_lower for word in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'hi']):
        return f"Olá! Bem-vindo ao {store_name}! 🍔 Como posso ajudar você hoje? Posso mostrar nosso cardápio, dar sugestões ou tirar dúvidas!"
    
    if any(word in message_lower for word in ['cardápio', 'cardapio', 'menu', 'produtos', 'o que tem', 'o que vocês tem']):
        produtos = Product.get_all(available_only=True)
        categorias = {}
        for p in produtos:
            cat = p.get('category_id', 'Outros')
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(p['name'])
        
        resposta = f"Nosso cardápio tem várias delícias! 🍔\n\n"
        if produtos:
            resposta += f"Alguns destaques:\n"
            for p in produtos[:5]:
                resposta += f"• {p['name']} - R$ {p['price']:.2f}\n"
            resposta += f"\nVisite nosso cardápio completo para ver todas as opções!"
        return resposta
    
    if any(word in message_lower for word in ['sugestão', 'sugestao', 'recomendar', 'recomenda', 'melhor', 'popular', 'favorito']):
        produtos = Product.get_all(available_only=True)
        if produtos:
            top_products = produtos[:3]
            resposta = "Nossas sugestões mais populares são:\n\n"
            for p in top_products:
                resposta += f"🍔 {p['name']} - R$ {p['price']:.2f}\n{p.get('description', '')}\n\n"
            return resposta
        return "Todos nossos produtos são deliciosos! Confira o cardápio completo."
    
    if any(word in message_lower for word in ['horário', 'horario', 'abre', 'fecha', 'funcionamento', 'aberto', 'abrir']):
        return f"Nosso horário de funcionamento é: {hours}\n\nEstamos ansiosos para receber você! 😊"
    
    if any(word in message_lower for word in ['endereço', 'endereco', 'localização', 'localizacao', 'onde', 'local', 'fica']):
        return f"Estamos localizados em:\n📍 {address}\n\nVenha nos visitar!"
    
    if any(word in message_lower for word in ['telefone', 'contato', 'ligar', 'whatsapp', 'zap']):
        return f"Você pode entrar em contato conosco:\n📞 {phone}\n\nEstamos à disposição!"
    
    if any(word in message_lower for word in ['pagamento', 'pagar', 'forma', 'cartão', 'cartao', 'dinheiro', 'pix']):
        return "Aceitamos as seguintes formas de pagamento:\n💳 Cartão de Crédito e Débito\n💵 Dinheiro\n📱 PIX\n\nEscolha a que for mais conveniente para você!"
    
    if any(word in message_lower for word in ['entrega', 'delivery', 'entregar', 'levar']):
        return f"Sim! Fazemos entregas! 🚗\n\nVocê pode fazer seu pedido pelo nosso site ou nos ligar no {phone}. Taxa de entrega pode variar conforme a região."
    
    if any(word in message_lower for word in ['preço', 'preco', 'valor', 'quanto custa', 'quanto é']):
        produtos = Product.get_all(available_only=True)
        if produtos:
            min_price = min(p['price'] for p in produtos)
            max_price = max(p['price'] for p in produtos)
            return f"Nossos preços variam de R$ {min_price:.2f} a R$ {max_price:.2f}. Temos opções para todos os gostos e bolsos! Confira o cardápio completo para ver todos os valores."
        return "Confira nosso cardápio para ver todos os preços!"
    
    if any(word in message_lower for word in ['vegetariano', 'vegano', 'vegetariana']):
        produtos = Product.get_all(available_only=True)
        vegetarian = [p for p in produtos if 'vegetar' in p['name'].lower() or 'vegano' in p['name'].lower()]
        if vegetarian:
            resposta = "Temos opções vegetarianas/veganas sim! 🌱\n\n"
            for p in vegetarian:
                resposta += f"• {p['name']} - R$ {p['price']:.2f}\n"
            return resposta
        return "Consulte nosso cardápio para ver as opções vegetarianas disponíveis!"
    
    if any(word in message_lower for word in ['obrigado', 'obrigada', 'valeu', 'thanks', 'brigadão']):
        return "Por nada! Foi um prazer ajudar! 😊 Se precisar de mais alguma coisa, estou aqui!"
    
    if any(word in message_lower for word in ['tchau', 'até logo', 'ate logo', 'até mais', 'ate mais', 'bye']):
        return f"Até logo! Esperamos ver você em breve no {store_name}! 👋🍔"
    
    return f"Olá! Sou o assistente virtual do {store_name}! 😊\n\nPosso ajudar com:\n• Informações sobre o cardápio\n• Sugestões de produtos\n• Horários de funcionamento\n• Formas de pagamento\n• Endereço e contato\n\nComo posso ajudar você?"

@chatbot.route('/')
def chat_page():
    return render_template('chatbot/chat.html')

@chatbot.route('/api/mensagem', methods=['POST'])
def send_message():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'success': False, 'error': 'Mensagem vazia'}), 400
    
    if model:
        try:
            SYSTEM_PROMPT = """
Você é um assistente virtual da Meatz Burger, uma hamburgueria moderna e acolhedora.
Seu papel é ajudar os clientes com:
- Informações sobre o cardápio
- Sugestões de produtos
- Horários de funcionamento
- Formas de pagamento aceitas
- Dúvidas gerais

Seja sempre cordial, prestativo e use uma linguagem amigável.
Responda de forma clara e objetiva.
"""
            chat = model.start_chat(history=[])
            full_prompt = f"{SYSTEM_PROMPT}\n\nCliente: {user_message}\nAssistente:"
            response = chat.send_message(full_prompt)
            bot_response = response.text
            
            return jsonify({
                'success': True,
                'response': bot_response
            })
        except Exception as e:
            bot_response = get_simple_response(user_message)
            return jsonify({
                'success': True,
                'response': bot_response
            })
    else:
        bot_response = get_simple_response(user_message)
        return jsonify({
            'success': True,
            'response': bot_response
        })

@chatbot.route('/api/sugestoes', methods=['GET'])
def get_suggestions():
    from app.db_operations import Product
    
    produtos = Product.get_all(available_only=True)
    return jsonify({
        'success': True,
        'suggestions': [p['name'] for p in produtos[:3]]
    })

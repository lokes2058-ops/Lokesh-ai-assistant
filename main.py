from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import google.generativeai as genai
import os

app = Flask(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

conversation_history = {}

SYSTEM_PROMPT = """Tu Lokesh ka personal AI assistant hai.

Tere baare mein:
- Tu bahut polite aur professional hai
- Tu Hindi aur English dono mein baat kar sakta hai
- Tu naturally baat karta hai, robotic nahi
- Har baar alag alag naturally baat kar

Jab koi call kare:
- Pehle greeting de: "Namaste! Main Lokesh ji ka assistant hun, aap kaise madad kar sakta hun?"
- Caller ki baat dhyan se suno
- Situation ke hisaab se naturally jawab do
- Agar koi important kaam ho ya caller insist kare to kaho: "Ji bilkul, main abhi Lokesh ji ko inform karta hun, kya aap thoda wait karenge?"
- Kabhi bhi same script mat repeat karo"""

@app.route("/incoming-call", methods=['POST'])
def incoming_call():
    call_sid = request.form.get('CallSid')
    conversation_history[call_sid] = []
    response = VoiceResponse()
    gather = Gather(input='speech', action='/handle-speech', method='POST',
                   language='hi-IN', speech_timeout='auto')
    gather.say("Namaste! Main Lokesh ji ka assistant hun, aap kaise madad kar sakta hun?",
               voice='Polly.Aditi', language='hi-IN')
    response.append(gather)
    return str(response)

@app.route("/handle-speech", methods=['POST'])
def handle_speech():
    call_sid = request.form.get('CallSid')
    caller_said = request.form.get('SpeechResult', '')
    if call_sid not in conversation_history:
        conversation_history[call_sid] = []
    conversation_history[call_sid].append(f"Caller: {caller_said}")
    history_text = "\n".join(conversation_history[call_sid])
    prompt = f"{SYSTEM_PROMPT}\n\nConversation:\n{history_text}\n\nAssistant:"
    ai_response = model.generate_content(prompt)
    ai_text = ai_response.text
    conversation_history[call_sid].append(f"Assistant: {ai_text}")
    response = VoiceResponse()
    gather = Gather(input='speech', action='/handle-speech', method='POST',
                   language='hi-IN', speech_timeout='auto')
    gather.say(ai_text, voice='Polly.Aditi', language='hi-IN')
    response.append(gather)
    return str(response)

@app.route("/call-status", methods=['POST'])
def call_status():
    call_sid = request.form.get('CallSid')
    if call_sid in conversation_history:
        del conversation_history[call_sid]
    return '', 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

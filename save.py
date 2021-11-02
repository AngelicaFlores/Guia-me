import json
import os
from dotenv import load_dotenv
from flask import Flask, Response
from flask import jsonify
from flask import request, redirect
from flask_socketio import SocketIO
from flask_cors import CORS
from ibm_watson import AssistantV1
from ibm_watson import SpeechToTextV1
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core import get_authenticator_from_environment

import assistant_setup

app = Flask(__name__)
socketio = SocketIO(app)
CORS(app)


# Redirect http to https on CloudFoundry
@app.before_request
def before_request():
    fwd = request.headers.get('x-forwarded-proto')

    # Not on Cloud Foundry
    if fwd is None:
        return None
    # On Cloud Foundry and is https
    elif fwd == "https":
        return None
    # On Cloud Foundry and is http, then redirect
    elif fwd == "http":
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

#Se muestra el index, ahi se ve la interfaz donde se muestran los mensajes escuchados por Speech-to-Text
#y la respuesta que Watson Assistant da. 
@app.route('/')
def Welcome():
    return app.send_static_file('index.html')

# Es la ruta que se utiliza para enviar y recibir mensajes desde Watson Assistant 
@app.route('/api/conversation', methods=['POST', 'GET'])
def getConvResponse():

    convText = request.form.get('convText')
    convContext = request.form.get('context', "{}")
    jsonContext = json.loads(convContext)

   # response = assistant.message(workspace_id=workspace_id,
    #                             input={'text': convText},
     #                            context=jsonContext
      #                           'options': {
       #                                     'return_context': True}
        #                        )
    message_stateless(self,
        assistant_id: str,
        *,
        input: 'MessageInputStateless' = None,
        context: 'MessageContextStateless' = None,
        user_id: str = None,
        **kwargs
    ) -> DetailedResponse

    print("mira aaa", DetailedResponse)

    #response = response.get_result()
    #reponseText = response["output"]["text"]
    #responseDetails = {'responseText': '... '.join(reponseText),
     #                  'context': response["context"]}
    #print("MIRA " , response)
    #return jsonify(results=responseDetails)


@app.route('/api/text-to-speech', methods=['POST'])
def getSpeechFromText():
    inputText = request.form.get('text')
    ttsService = TextToSpeechV1()

    def generate():
        if inputText:
            audioOut = ttsService.synthesize(
                inputText,
                accept='audio/wav',
                voice='es-LA_SofiaV3Voice').get_result()

            data = audioOut.content
        else:
            print("Empty response")
            data = "No tengo una respuesta para eso."

        yield data

    return Response(response=generate(), mimetype="audio/x-wav")


@app.route('/api/speech-to-text', methods=['POST'])
def getTextFromSpeech():

    sttService = SpeechToTextV1()

    response = sttService.recognize(
            audio=request.get_data(cache=False),
            content_type='audio/wav',
            model="es-MX_BroadbandModel", #Espaniol
            timestamps=True,
            word_confidence=True,
            smart_formatting=True).get_result()

    # Ask user to repeat if STT can't transcribe the speech
    if len(response['results']) < 1:
        return Response(mimetype='plain/text',
                        response="Lo siento, no entendi, ¿podrías repetirlo?")

    text_output = response['results'][0]['alternatives'][0]['transcript']
    text_output = text_output.strip()
    return Response(response=text_output, mimetype='plain/text')


port = os.environ.get("PORT") or os.environ.get("VCAP_APP_PORT") or 5000
if __name__ == "__main__":
    load_dotenv()

    # SDK is currently confused. Only sees 'conversation' for CloudFoundry.
    
    authenticator = (get_authenticator_from_environment('assistant') or
                     get_authenticator_from_environment('conversation'))
    assistant = AssistantV1(version="2021-06-14", authenticator=authenticator)
    workspace_id = assistant_setup.init_skill(assistant)
    
    socketio.run(app, host='0.0.0.0', port=int(port))

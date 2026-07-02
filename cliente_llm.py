import time
import requests
import os
from dotenv import load_dotenv
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.prompts import ChatPromptTemplate


class ColabChatModel(BaseChatModel):
    url_llm: str

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Adapts the LangChain message objects to the format expected by the remote FastAPI chat endpoint.
        """
        payload_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                role = "user"
            payload_messages.append({"role": role, "content": msg.content})

        try:
            response = requests.post(
                f"{self.url_llm}/chat",
                json={"messages": payload_messages},
                headers={"Content-Type": "application/json"}
            ).json()
            content = response.get("response", "respuesta no obtenida")
        except Exception as e:
            print(f"Error en la petición al servidor LLM: {e}")
            content = "respuesta no obtenida"

        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])

    def with_structured_output(
        self,
        schema: Any,
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Custom implementation of with_structured_output using PydanticOutputParser.
        Allows calling `model.with_structured_output(SchemaClass)` natively.
        """
        from langchain_core.output_parsers import PydanticOutputParser
        from langchain_core.runnables import RunnableLambda

        parser = PydanticOutputParser(pydantic_object=schema)
        format_instructions = parser.get_format_instructions()

        def structured_chain(prompt_value):
            if hasattr(prompt_value, "to_messages"):
                messages = prompt_value.to_messages()
            elif isinstance(prompt_value, list):
                messages = prompt_value
            else:
                messages = [HumanMessage(content=str(prompt_value))]

            # Inject the formatting instructions to the last message content
            if messages:
                last_msg = messages[-1]
                if "Instrucciones de formato:" not in last_msg.content:
                    last_msg.content += f"\n\nInstrucciones de formato:\n{format_instructions}"

            # Invoke the custom chat model using standard invoke
            response_msg = self.invoke(messages)
            
            # Parse the text response to the Pydantic schema
            parsed = parser.parse(response_msg.content)
            return parsed

        return RunnableLambda(structured_chain)

    @property
    def _llm_type(self) -> str:
        return "colab_chat_model"


class ClienteLLM:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("URL_LLM")
        self.model = ColabChatModel(url_llm=self.url)

    def generar_salida(self, system_prompt: str, user_message: str):
        """
        Llama al LLM usando LangChain con un system prompt y un user message.
        Retorna (respuesta: str, tiempo: float).
        """
        # Crear la plantilla de chat
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{user_message}")
        ])

        # Construir la cadena LCEL (LangChain Expression Language)
        chain = prompt | self.model

        inicio = time.time()
        try:
            response = chain.invoke({"user_message": user_message})
            tiempo = time.time() - inicio
            return response.content, tiempo
        except Exception as e:
            tiempo = time.time() - inicio
            print(f"Error al invocar la cadena de LangChain: {e}")
            return "respuesta no obtenida", tiempo

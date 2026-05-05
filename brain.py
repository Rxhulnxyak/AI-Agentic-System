import asyncio
from typing import Optional, List, Dict, Any
from mistralai.client import Mistral
from logger import logger
from config import settings
from utils import handle_errors, time_it
from prompts import SYSTEM_PROMPT
from memory import Memory

class Brain:
    """The cognitive engine of Kolimarii, supports Anthropic and Mistral."""

    def __init__(self, memory: Optional[Memory] = None, planner: Optional['Planner'] = None):
        self.client = None
        self.provider = None
        self.history: List[Dict[str, Any]] = []
        self.memory = memory or Memory()
        self.planner = planner
        
        # Check Anthropic
        if settings.ai.anthropic_api_key and "your_" not in settings.ai.anthropic_api_key:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=settings.ai.anthropic_api_key)
            self.provider = "anthropic"
            self.model = settings.ai.model_name if "claude" in settings.ai.model_name else "claude-3-5-sonnet-20240620"
            logger.success(f"Brain active with Anthropic: {self.model}")
        # Check OpenAI
        elif settings.ai.openai_api_key and "your_" not in settings.ai.openai_api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.ai.openai_api_key)
            self.provider = "openai"
            self.model = settings.ai.model_name if "gpt" in settings.ai.model_name else "gpt-4o"
            logger.success(f"Brain active with OpenAI: {self.model}")
        # Check Mistral
        elif settings.ai.mistral_api_key and "your_" not in settings.ai.mistral_api_key:
            self.client = Mistral(api_key=settings.ai.mistral_api_key)
            self.provider = "mistral"
            self.model = settings.ai.model_name if "mistral" in settings.ai.model_name else "mistral-large-latest"
            logger.success(f"Brain active with Mistral: {self.model}")
        else:
            logger.error("No valid AI API Key found (Anthropic, OpenAI, or Mistral) in .env")

    @handle_errors("Brain")
    @time_it
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Processes query with support for multi-step tools and multiple providers."""
        if not self.client:
            return {"text": "I need an API key (Anthropic, OpenAI, or Mistral) to think. Please check your .env file.", "tool_calls": []}

        # Retrieve memories
        relevant_memories = self.memory.search(query)
        memory_context = ""
        if relevant_memories:
            memory_context = "\nUser Context/History:\n- " + "\n- ".join(relevant_memories)

        augmented_system_prompt = SYSTEM_PROMPT + memory_context
        
        if self.provider == "anthropic":
            return await self._process_anthropic(query, augmented_system_prompt)
        elif self.provider == "openai":
            return await self._process_openai(query, augmented_system_prompt)
        elif self.provider == "mistral":
            return await self._process_mistral(query, augmented_system_prompt)

    async def _process_openai(self, query: str, system_prompt: str) -> Dict[str, Any]:
        if not self.history:
            self.history.append({"role": "system", "content": system_prompt})
        
        self.history.append({"role": "user", "content": query})
        
        max_loops = 5
        current_loop = 0
        final_text = ""
        all_tool_calls = []

        while current_loop < max_loops:
            current_loop += 1
            tools = []
            if self.planner:
                for t in self.planner.get_tool_schemas():
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t["description"],
                            "parameters": t["parameters"]
                        }
                    })

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=self.history,
                tools=tools if tools else None,
                tool_choice="auto"
            )

            msg = response.choices[0].message
            self.history.append(msg)
            
            if msg.content:
                final_text = msg.content
            
            if not msg.tool_calls:
                break
            
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                import json
                args = json.loads(tool_call.function.arguments)
                logger.info(f"OpenAI executing tool: {name}")
                result = await self.planner.execute_tool(name, args)
                
                self.history.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call.id
                })
                all_tool_calls.append({"id": tool_call.id, "name": name, "input": args})

        if final_text: self.memory.add_episodic(f"User: {query} | Kolimarii: {final_text}")
        return {"text": final_text, "tool_calls": all_tool_calls}

    async def _process_anthropic(self, query: str, system_prompt: str) -> Dict[str, Any]:
        self.history.append({"role": "user", "content": query})
        max_loops = 5
        current_loop = 0
        final_text = ""
        all_tool_calls = []

        while current_loop < max_loops:
            current_loop += 1
            tools = []
            if self.planner:
                for t in self.planner.get_tool_schemas():
                    tools.append({"name": t["name"], "description": t["description"], "input_schema": t["parameters"]})

            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=self.history,
                tools=tools if tools else None
            )

            assistant_content = []
            has_tool_use = False
            current_response_text = ""
            current_tool_calls = []

            for content in response.content:
                if content.type == "text":
                    current_response_text += content.text
                    assistant_content.append({"type": "text", "text": content.text})
                elif content.type == "tool_use":
                    has_tool_use = True
                    current_tool_calls.append({"id": content.id, "name": content.name, "input": content.input})
                    assistant_content.append({"type": "tool_use", "id": content.id, "name": content.name, "input": content.input})
            
            self.history.append({"role": "assistant", "content": assistant_content})
            final_text = current_response_text
            all_tool_calls.extend(current_tool_calls)

            if not has_tool_use: break

            tool_results = []
            for tool in current_tool_calls:
                result = await self.planner.execute_tool(tool["name"], tool["input"])
                tool_results.append({"type": "tool_result", "tool_use_id": tool["id"], "content": str(result)})
            
            self.history.append({"role": "user", "content": tool_results})

        if final_text: self.memory.add_episodic(f"User: {query} | Kolimarii: {final_text}")
        return {"text": final_text, "tool_calls": all_tool_calls}

    async def _process_mistral(self, query: str, system_prompt: str) -> Dict[str, Any]:
        # Mistral uses standard OpenAI-like messages
        if not self.history:
            self.history.append({"role": "system", "content": system_prompt})
        
        self.history.append({"role": "user", "content": query})
        
        max_loops = 5
        current_loop = 0
        final_text = ""
        all_tool_calls = []

        while current_loop < max_loops:
            current_loop += 1
            tools = []
            if self.planner:
                for t in self.planner.get_tool_schemas():
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t["description"],
                            "parameters": t["parameters"]
                        }
                    })

            response = await asyncio.to_thread(
                self.client.chat.complete,
                model=self.model,
                messages=self.history,
                tools=tools if tools else None,
                tool_choice="auto"
            )

            msg = response.choices[0].message
            self.history.append(msg)
            
            if msg.content:
                final_text = msg.content
            
            if not msg.tool_calls:
                break
            
            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                import json
                args = json.loads(tool_call.function.arguments)
                logger.info(f"Mistral executing tool: {name}")
                result = await self.planner.execute_tool(name, args)
                
                self.history.append({
                    "role": "tool",
                    "name": name,
                    "content": str(result),
                    "tool_call_id": tool_call.id
                })
                all_tool_calls.append({"id": tool_call.id, "name": name, "input": args})

        if final_text: self.memory.add_episodic(f"User: {query} | Kolimarii: {final_text}")
        return {"text": final_text, "tool_calls": all_tool_calls}

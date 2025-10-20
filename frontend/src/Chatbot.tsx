import ChatbotPanel  from "./pages/Assistant";

export default function AssistantDrawer() {
  return (
    <ChatbotPanel
      modelName="TinyLlama"
      onClose={() => {/* fermer le panel */}}
      onSend={() => {/* envoyer le message */}}
      onChipTopSkills={() => {/* prompt: top skills */}}
      onChipSalary={() => {/* prompt: salary trends */}}
      onChipRemote={() => {/* prompt: remote jobs */}}
      className="max-w-[450px]" // optionnel
    />
  );
}

import { ChatWindow } from "./components/ChatWindow";
import { ErrorBoundary } from "./components/ErrorBoundary";

export default function App() {
  return (
    <ErrorBoundary>
      <ChatWindow />
    </ErrorBoundary>
  );
}

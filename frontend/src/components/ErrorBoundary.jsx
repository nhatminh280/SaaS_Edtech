import { Component } from "react";

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("Chat UI error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            margin: 16,
            padding: 14,
            border: "1px solid #F0997B",
            borderRadius: 8,
            background: "#FAECE7",
            color: "#712B13",
            fontSize: 14,
          }}
        >
          Giao diện chat gặp lỗi. Tải lại trang để thử lại.
        </div>
      );
    }

    return this.props.children;
  }
}

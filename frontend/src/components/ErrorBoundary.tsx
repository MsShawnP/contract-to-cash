import { Component, type ReactNode } from "react";

interface Props {
  section: string;
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <section className="section">
          <p className="section-body">
            This section could not be rendered. Data may be unavailable.
          </p>
        </section>
      );
    }
    return this.props.children;
  }
}

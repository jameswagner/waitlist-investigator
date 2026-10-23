import { render, screen } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import App from "./App";

it("renders the screen with the demo label, chat and empty history", () => {
  vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("offline"))));
  render(<App />);
  expect(screen.getByRole("heading", { name: "Synthetic waitlist analytics demo" })).toBeInTheDocument();
  expect(screen.getByLabelText("Agent chat")).toBeInTheDocument();
  expect(screen.getByText("No completed queries.")).toBeInTheDocument();
});

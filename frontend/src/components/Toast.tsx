"use client";

interface ToastProps {
  type: "success" | "error";
  message: string;
}

export default function Toast({ type, message }: ToastProps) {
  return <div className={`toast ${type}`}>{message}</div>;
}

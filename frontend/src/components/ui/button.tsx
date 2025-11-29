import * as React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline";
};

export const Button: React.FC<ButtonProps> = ({
  className = "",
  variant = "default",
  ...props
}) => {
  const base =
    "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none h-9 px-4 py-2";
  const variants: Record<string, string> = {
    default:
      "bg-sky-500 text-white hover:bg-sky-600 focus-visible:ring-sky-400 ring-offset-slate-900",
    outline:
      "border border-slate-700 bg-transparent text-slate-100 hover:bg-slate-800 focus-visible:ring-slate-500 ring-offset-slate-900",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      {...props}
    />
  );
};

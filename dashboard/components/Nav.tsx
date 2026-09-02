"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const LINKS = [
  { href: "/ask", label: "Ask" },
  { href: "/", label: "Overview" },
  { href: "/queries", label: "Live Queries" },
  { href: "/runs", label: "Eval Runs" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="border-b" style={{ borderColor: "var(--border)" }}>
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center gap-8">
        <span className="font-semibold tracking-tight">
          RAG Evaluation Platform
        </span>
        <nav className="flex gap-1">
          {LINKS.map((link) => {
            const active =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  "px-3 py-1.5 rounded-md text-sm transition-colors",
                  active
                    ? "font-medium"
                    : "secondary hover:text-[var(--text-primary)]"
                )}
                style={
                  active
                    ? { background: "var(--surface)", border: "1px solid var(--border)" }
                    : undefined
                }
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

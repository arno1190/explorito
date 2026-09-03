import { AlertTriangle, Flag, Lightbulb } from "lucide-react";

import { cn } from "@/lib/utils";
import type { ValidationIssue } from "@/lib/api/model";

import { issueRow, severityStyle } from "../_lib/contrib";

const ICONS = {
  error: AlertTriangle,
  warning: Lightbulb,
  flag: Flag,
} as const;

/**
 * Liste de constats du validateur. `anchor` reste affichable : un même
 * composant sert au bandeau d'envoi (constats groupés) et à l'affichage
 * ancré sous la leçon ou l'exercice fautif (`showAnchor={false}`).
 */
export function IssueList({
  issues,
  showAnchor = true,
  className,
}: {
  issues: ValidationIssue[];
  showAnchor?: boolean;
  className?: string;
}) {
  if (issues.length === 0) return null;
  return (
    <ul className={cn("space-y-2", className)}>
      {issues.map((issue, index) => {
        const style = severityStyle(issue.severity);
        const { anchor, message } = issueRow(issue);
        const Icon = ICONS[issue.severity as keyof typeof ICONS] ?? Lightbulb;
        return (
          <li
            key={`${issue.code}-${index}`}
            className={cn(
              "flex items-start gap-3 rounded-xl border-2 p-3 text-sm text-fun-text",
              style.box
            )}
          >
            <Icon className="mt-0.5 h-4 w-4 shrink-0 text-fun-text" />
            <div className="min-w-0 flex-1">
              <span
                className={cn(
                  "mr-2 inline-block rounded-full px-2 py-0.5 text-xs font-bold",
                  style.chip
                )}
              >
                {style.label}
              </span>
              {showAnchor && anchor && (
                <span className="font-bold">{anchor} : </span>
              )}
              <span>{message}</span>
              {issue.field && (
                <span className="ml-1 font-mono text-xs text-fun-text-muted">
                  ({issue.field})
                </span>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

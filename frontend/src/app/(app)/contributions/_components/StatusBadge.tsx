import { cn } from "@/lib/utils";
import type { CommunityStatus } from "@/lib/api/model";

import { statusStyle } from "../_lib/contrib";

export function StatusBadge({
  status,
  className,
}: {
  status: CommunityStatus;
  className?: string;
}) {
  const style = statusStyle(status);
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-xs font-bold",
        style.className,
        className
      )}
    >
      {style.label}
    </span>
  );
}

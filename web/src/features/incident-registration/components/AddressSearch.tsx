/**
 * Step 2 — address search with debounced autocomplete, keyboard navigation
 * (↑/↓ + Enter) and mouse selection. On selection the address is reverse-
 * geocoded to district / settlement and stored as the incident location.
 */
import { memo, useCallback, useEffect, useRef, useState } from "react";
import { MapPin, Search, Loader2, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAddressSearch, useResolveAddress } from "../hooks";
import { useRegistrationStore } from "../store/registration.store";
import type { AddressCandidate } from "../types";

function AddressSearchBase() {
  const [term, setTerm] = useState("");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const { data: candidates = [], isFetching } = useAddressSearch(term);
  const { resolve, isResolving } = useResolveAddress();
  const location = useRegistrationStore((s) => s.location);

  // Close the dropdown on outside click.
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  useEffect(() => setHighlight(0), [candidates]);

  const choose = useCallback(
    async (candidate: AddressCandidate) => {
      setTerm(candidate.formatted_address);
      setOpen(false);
      await resolve(candidate);
    },
    [resolve],
  );

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!open || candidates.length === 0) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setHighlight((h) => Math.min(h + 1, candidates.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setHighlight((h) => Math.max(h - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        const c = candidates[highlight];
        if (c) void choose(c);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    },
    [open, candidates, highlight, choose],
  );

  return (
    <div ref={containerRef} className="relative flex flex-col gap-1">
      <Label htmlFor="addressSearch">Адрес происшествия *</Label>
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          id="addressSearch"
          value={term}
          onChange={(e) => {
            setTerm(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Введите улицу, дом, ориентир…"
          className="h-12 pl-9 pr-9 text-base"
          role="combobox"
          aria-expanded={open}
          aria-controls="address-listbox"
          aria-autocomplete="list"
          autoComplete="off"
        />
        {(isFetching || isResolving) && (
          <Loader2
            className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground"
            aria-hidden
          />
        )}
      </div>

      {open && term.trim().length >= 3 && (
        <ul
          id="address-listbox"
          role="listbox"
          className="absolute top-full z-30 mt-1 max-h-72 w-full overflow-y-auto rounded-md border border-border bg-panel shadow-xl"
        >
          {candidates.length === 0 && !isFetching ? (
            <li className="px-3 py-2 text-sm text-muted-foreground">
              Адрес не найден. Уточните запрос.
            </li>
          ) : (
            candidates.map((c, i) => (
              <li
                key={c.id}
                role="option"
                aria-selected={i === highlight}
                onMouseEnter={() => setHighlight(i)}
                onMouseDown={(e) => {
                  e.preventDefault();
                  void choose(c);
                }}
                className={cn(
                  "flex cursor-pointer items-start gap-2 px-3 py-2 text-sm",
                  i === highlight ? "bg-muted" : "hover:bg-muted/60",
                )}
              >
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-info" aria-hidden />
                <span className="flex-1">{c.formatted_address}</span>
              </li>
            ))
          )}
        </ul>
      )}

      {location && (
        <div className="mt-1 flex items-start gap-2 rounded-md border border-success/40 bg-success/5 px-3 py-2 text-xs">
          <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" aria-hidden />
          <div className="flex flex-col gap-0.5">
            <span className="font-medium">{location.address}</span>
            <span className="tabular-nums text-muted-foreground">
              {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
            </span>
            {location.area?.district && (
              <span className="text-muted-foreground">
                Район: {location.area.district}
                {location.area.settlement ? ` · ${location.area.settlement}` : ""}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export const AddressSearch = memo(AddressSearchBase);

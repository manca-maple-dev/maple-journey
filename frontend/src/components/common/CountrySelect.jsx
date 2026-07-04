import { useState } from "react";
import { Check, ChevronsUpDown, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { cn } from "@/lib/utils";

// Common source countries for Canadian newcomers first, then the rest A–Z.
export const COUNTRIES = [
  { name: "India", flag: "🇮🇳" }, { name: "Nigeria", flag: "🇳🇬" }, { name: "Philippines", flag: "🇵🇭" },
  { name: "China", flag: "🇨🇳" }, { name: "Pakistan", flag: "🇵🇰" }, { name: "Brazil", flag: "🇧🇷" },
  { name: "Iran", flag: "🇮🇷" }, { name: "France", flag: "🇫🇷" }, { name: "United Kingdom", flag: "🇬🇧" },
  { name: "United States", flag: "🇺🇸" }, { name: "Mexico", flag: "🇲🇽" }, { name: "Ukraine", flag: "🇺🇦" },
  { name: "Afghanistan", flag: "🇦🇫" }, { name: "Bangladesh", flag: "🇧🇩" }, { name: "Colombia", flag: "🇨🇴" },
  { name: "Egypt", flag: "🇪🇬" }, { name: "Ethiopia", flag: "🇪🇹" }, { name: "Germany", flag: "🇩🇪" },
  { name: "Ghana", flag: "🇬🇭" }, { name: "Kenya", flag: "🇰🇪" }, { name: "Morocco", flag: "🇲🇦" },
  { name: "Nepal", flag: "🇳🇵" }, { name: "South Korea", flag: "🇰🇷" }, { name: "Sri Lanka", flag: "🇱🇰" },
  { name: "Syria", flag: "🇸🇾" }, { name: "Vietnam", flag: "🇻🇳" }, { name: "Algeria", flag: "🇩🇿" },
  { name: "Argentina", flag: "🇦🇷" }, { name: "Australia", flag: "🇦🇺" }, { name: "Cameroon", flag: "🇨🇲" },
  { name: "Chile", flag: "🇨🇱" }, { name: "Cuba", flag: "🇨🇺" }, { name: "Ecuador", flag: "🇪🇨" },
  { name: "Eritrea", flag: "🇪🇷" }, { name: "Indonesia", flag: "🇮🇩" }, { name: "Iraq", flag: "🇮🇶" },
  { name: "Ireland", flag: "🇮🇪" }, { name: "Israel", flag: "🇮🇱" }, { name: "Italy", flag: "🇮🇹" },
  { name: "Jamaica", flag: "🇯🇲" }, { name: "Japan", flag: "🇯🇵" }, { name: "Jordan", flag: "🇯🇴" },
  { name: "Lebanon", flag: "🇱🇧" }, { name: "Malaysia", flag: "🇲🇾" },
  { name: "Netherlands", flag: "🇳🇱" }, { name: "New Zealand", flag: "🇳🇿" }, { name: "Peru", flag: "🇵🇪" },
  { name: "Poland", flag: "🇵🇱" }, { name: "Portugal", flag: "🇵🇹" }, { name: "Romania", flag: "🇷🇴" },
  { name: "Russia", flag: "🇷🇺" }, { name: "Saudi Arabia", flag: "🇸🇦" }, { name: "Senegal", flag: "🇸🇳" },
  { name: "Somalia", flag: "🇸🇴" }, { name: "South Africa", flag: "🇿🇦" }, { name: "Spain", flag: "🇪🇸" },
  { name: "Sudan", flag: "🇸🇩" }, { name: "Taiwan", flag: "🇹🇼" }, { name: "Tanzania", flag: "🇹🇿" },
  { name: "Thailand", flag: "🇹🇭" }, { name: "Tunisia", flag: "🇹🇳" }, { name: "Turkey", flag: "🇹🇷" },
  { name: "Uganda", flag: "🇺🇬" }, { name: "United Arab Emirates", flag: "🇦🇪" }, { name: "Venezuela", flag: "🇻🇪" },
  { name: "Zimbabwe", flag: "🇿🇼" }, { name: "Other", flag: "🌍" },
];

const ALIASES = {
  "United Kingdom": "UK Britain England Scotland Wales",
  "United States": "USA US America",
  "United Arab Emirates": "UAE Dubai Abu Dhabi",
  "South Korea": "Korea",
  "Russia": "Russian Federation",
};

export function CountrySelect({ value, onChange, testId = "signup-country" }) {
  const [open, setOpen] = useState(false);
  const selected = COUNTRIES.find((c) => c.name === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          data-testid={testId}
          className="h-10 w-full justify-between font-normal"
        >
          <span className={cn("flex items-center gap-2 truncate", !selected && "text-muted-foreground")}>
            {selected ? <><span>{selected.flag}</span>{selected.name}</> : <><Search className="h-4 w-4" /> Search your country…</>}
          </span>
          <ChevronsUpDown className="h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
        <Command>
          <CommandInput placeholder="Type to search…" data-testid="country-search-input" />
          <CommandList>
            <CommandEmpty>No country found.</CommandEmpty>
            <CommandGroup>
              {COUNTRIES.map((c) => (
                <CommandItem
                  key={c.name}
                  value={`${c.name} ${ALIASES[c.name] || ""}`}
                  data-testid={`country-option-${c.name}`}
                  onSelect={() => { onChange(c.name); setOpen(false); }}
                >
                  <span className="mr-2">{c.flag}</span>
                  {c.name}
                  {value === c.name && <Check className="ml-auto h-4 w-4 text-brand-500" />}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

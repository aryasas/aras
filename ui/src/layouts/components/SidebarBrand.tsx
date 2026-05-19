export function SidebarBrand() {
  return (
    <header className="col-start-1 row-start-1 flex h-16 items-center justify-center border-b border-[var(--aras-border)] bg-[var(--aras-panel)] shadow-sm max-sm:h-[58px] max-sm:justify-start max-sm:px-4">
      <div
        className="relative flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-[var(--aras-radius)] border border-[color-mix(in_srgb,var(--aras-accent)_34%,transparent)] bg-[var(--aras-accent)] shadow-sm max-sm:h-9 max-sm:w-9"
        aria-label="Aras logo"
      >
        <span className="font-serif text-[31px] font-black leading-none text-white max-sm:text-[26px]">
          A
        </span>
        <span className="absolute bottom-[12px] left-[15px] h-[3px] w-[13px] rounded-full bg-white/90 max-sm:bottom-[10px] max-sm:left-[13px] max-sm:w-[11px]" />
      </div>
      <span className="ml-2 hidden text-[27px] font-bold tracking-wide text-[var(--aras-accent)] max-sm:inline">Aras</span>
    </header>
  )
}

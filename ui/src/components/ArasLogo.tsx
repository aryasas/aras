type ArasLogoProps = {
  size?: 'sm' | 'md' | 'lg'
  showWordmark?: boolean
}

const sizeClasses = {
  sm: {
    mark: 'h-8 w-8 rounded-[calc(var(--app-radius)*0.6)]',
    letter: 'text-[20px]',
    word: 'text-[20px]',
  },
  md: {
    mark: 'h-[42px] w-[42px] rounded-[calc(var(--app-radius)*0.7)]',
    letter: 'text-[27px]',
    word: 'text-[27px]',
  },
  lg: {
    mark: 'h-16 w-16 rounded-[var(--app-radius)]',
    letter: 'text-[40px]',
    word: 'text-[32px]',
  },
}

export function ArasLogo({ size = 'md', showWordmark = false }: ArasLogoProps) {
  const classes = sizeClasses[size]

  return (
    <div className="flex items-center gap-2" aria-label="Aras logo">
      <div
        className={`${classes.mark} flex shrink-0 items-center justify-center bg-[var(--app-accent)] font-bold text-white shadow-sm`}
      >
        <span className={`${classes.letter} leading-none`}>A</span>
      </div>
      {showWordmark && (
        <span className={`${classes.word} hidden font-bold tracking-normal text-[var(--app-accent)] max-sm:inline`}>
          Aras
        </span>
      )}
    </div>
  )
}

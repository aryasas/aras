// @ts-nocheck
import { readFileSync } from 'node:fs'

const readConfigView = (name: string) => readFileSync(new URL(`../${name}.tsx`, import.meta.url), 'utf8')
const readLib = () => readFileSync(new URL('../../../lib/config.ts', import.meta.url), 'utf8')

describe('ConfigPage wiring', () => {
  it('loads sections and switches the active section', () => {
    const source = readConfigView('ConfigPage')

    expect(source).toContain('useSections')
    expect(source).toContain('setSelectedKey(item.key)')
    expect(source).toContain('core_config.company')
  })

  it('saves section values and keeps secrets masked', () => {
    const form = readConfigView('SectionForm')

    expect(form).toContain('useSaveSection')
    expect(form).toContain("values[field.key] === '••••'")
    expect(form).toContain('Rotate')
  })

  it('validates client-side before server save', () => {
    const form = readConfigView('SectionForm')

    expect(form).toContain('validateAll')
    expect(form).toContain('must be a number')
    expect(form).toContain('Use a hex color')
  })

  it('uses React Query cache invalidation for config mutations', () => {
    const source = readLib()

    expect(source).toContain('useMutation')
    expect(source).toContain("invalidateQueries({ queryKey: ['config'] })")
  })
})

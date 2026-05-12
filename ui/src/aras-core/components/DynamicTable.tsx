import ListView from './ListView'

const DynamicTable = ({ resource }: { resource: string }) => {
  return <ListView resource={resource} />
}

export default DynamicTable

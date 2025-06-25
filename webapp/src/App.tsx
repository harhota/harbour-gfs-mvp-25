import React, { useState, useEffect } from 'react'
import { Theme, Button, TextField, TextArea, Flex, Heading, Text } from '@radix-ui/themes'
import { useUploadFile, useReadFile, useDeleteFile, useFileSize } from './hooks'

export default function App() {
  const [filename, setFilename] = useState('')
  const [content, setContent] = useState('')
  const [message, setMessage] = useState('')

  const uploadMutation = useUploadFile()
  const deleteMutation = useDeleteFile()
  const readQuery = useReadFile(filename, false)
  const { error: readQueryError } = readQuery
  const sizeQuery = useFileSize(filename, false)

  useEffect(() => {
    if (readQuery.data !== undefined) {
      setContent(readQuery.data)
    }
  }, [readQuery.data])

  const handleUpload = async () => {
    setMessage('')
    try {
      await uploadMutation.mutateAsync({ filename, data: content })
      setMessage('File uploaded')
    } catch (e: any) {
      setMessage(e.message)
    }
  }

  const handleRead = async () => {
    setMessage('')
    try {
      await readQuery.refetch()
    } catch (e: any) {
      setMessage(e.message)
    }
  }

  const handleDelete = async () => {
    setMessage('')
    try {
      await deleteMutation.mutateAsync(filename)
      setMessage('File deleted')
    } catch (e: any) {
      setMessage(e.message)
    }
  }

  const handleSize = async () => {
    setMessage('')
    try {
      await sizeQuery.refetch()
    } catch (e: any) {
      setMessage(e.message)
    }
  }

  return (
    <div>
      <Heading>Harbour DFS Client</Heading>
      <Flex direction="column" gap="3" style={{ maxWidth: 600, margin: '0 auto', padding: '1rem' }}>
        <TextField.Root placeholder="Filename" value={filename} onChange={(e) => setFilename(e.target.value)} />
        <TextArea placeholder="File contents" value={content} onChange={(e) => setContent(e.target.value)} rows={10} />
        <Flex gap="2" wrap="wrap">
          <Button onClick={handleUpload}>Upload</Button>
          <Button onClick={handleRead}>Read</Button>
          <Button onClick={handleDelete}>Delete</Button>
          <Button onClick={handleSize}>Size</Button>
        </Flex>
        {sizeQuery.data !== undefined && <Text size="2">Size: {sizeQuery.data}</Text>}
        {readQueryError && (
          <Text size="2" color="red">
            {readQueryError.message}
          </Text>
        )}
        {sizeQuery.error && (
          <Text size="2" color="red">
            {sizeQuery.error.message}
          </Text>
        )}
        {message && <Text size="2">{message}</Text>}
      </Flex>
    </div>
  )
}

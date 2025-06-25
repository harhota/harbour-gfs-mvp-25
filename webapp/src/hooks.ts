import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { uploadFileRequest, readFileRequest, deleteFileRequest, fileSizeRequest } from './api'

export function useUploadFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ filename, data }: { filename: string; data: string }) => uploadFileRequest(filename, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['file'] })
      queryClient.invalidateQueries({ queryKey: ['size'] })
    },
    onError: () => {
      queryClient.invalidateQueries({ queryKey: ['file'] })
      queryClient.invalidateQueries({ queryKey: ['size'] })
    },
  })
}

export function useReadFile(filename: string, enabled = false) {
  return useQuery({
    queryKey: ['file', filename],
    queryFn: () => readFileRequest(filename),
    enabled,
  })
}

export function useDeleteFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (filename: string) => deleteFileRequest(filename),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['file'] })
      queryClient.invalidateQueries({ queryKey: ['size'] })
    },
  })
}

export function useFileSize(filename: string, enabled = false) {
  return useQuery({
    queryKey: ['size', filename],
    queryFn: () => fileSizeRequest(filename),
    enabled,
  })
}

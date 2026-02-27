import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/api/client';

export const useImageSource = () => {
  const queryClient = useQueryClient();

  // GET current image source
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['image-source'],
    queryFn: async () => {
      const response = await apiClient.get('/services/config/image-source');
      return response.data.image_album_source as 'spotify' | 'lastfm';
    },
    staleTime: 60000,
  });

  // PATCH update image source
  const mutation = useMutation({
    mutationFn: async (newSource: 'spotify' | 'lastfm') => {
      const response = await apiClient.patch('/services/config/image-source', {
        image_album_source: newSource,
      });
      return response.data.image_album_source as 'spotify' | 'lastfm';
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['image-source'] });
    },
  });

  return {
    imageSource: data,
    isLoading,
    isError,
    refetch,
    setImageSource: mutation.mutate,
    isSaving: mutation.isPending,
  };
};

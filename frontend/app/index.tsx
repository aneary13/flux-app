import { View, Text, ActivityIndicator, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { apiClient } from '@/src/api/client';

interface RootResponse {
  status: string;
  version: string;
}

export default function HomeScreen() {
  const router = useRouter();

  const { data, isLoading, error } = useQuery<RootResponse>({
    queryKey: ['root'],
    queryFn: async () => {
      const response = await apiClient.get<RootResponse>('/');
      return response.data;
    },
  });

  return (
    <View className="flex-1 items-center justify-center bg-white p-6">
      <Text className="text-3xl font-bold mb-8 text-gray-900">
        FLUX App
      </Text>

      {isLoading && (
        <View className="items-center">
          <ActivityIndicator size="large" color="#3b82f6" />
          <Text className="mt-4 text-gray-600">Loading API version...</Text>
        </View>
      )}

      {error && (
        <View className="items-center">
          <Text className="text-red-600 text-lg font-semibold mb-2">
            Error loading API
          </Text>
          <Text className="text-red-500 text-sm">
            {error instanceof Error ? error.message : 'Unknown error'}
          </Text>
        </View>
      )}

      {data && (
        <View className="items-center mb-8">
          <Text className="text-gray-700 text-lg mb-2">API Status:</Text>
          <Text className="text-2xl font-bold text-green-600 mb-2">
            {data.status.toUpperCase()}
          </Text>
          <Text className="text-gray-700 text-lg mb-2">API Version:</Text>
          <Text className="text-xl font-semibold text-blue-600">
            {data.version}
          </Text>
        </View>
      )}

      <TouchableOpacity
        onPress={() => router.push('/check-in')}
        className="bg-blue-600 px-8 py-4 rounded-lg shadow-lg active:bg-blue-700"
      >
        <Text className="text-white text-lg font-semibold">Check In</Text>
      </TouchableOpacity>
    </View>
  );
}

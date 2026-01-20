import { View, Text, ActivityIndicator, ScrollView, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { apiClient, SessionPlan } from '@/src/api/client';

export default function WorkoutPlanScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  
  // Parse route parameters safely
  const pain = parseInt(params.pain as string, 10) || 0;
  const energy = parseInt(params.energy as string, 10) || 0;

  // Validate range
  const validPain = Math.max(0, Math.min(10, pain));
  const validEnergy = Math.max(0, Math.min(10, energy));

  const { data, isLoading, error, refetch } = useQuery<SessionPlan>({
    queryKey: ['workout-recommend', validPain, validEnergy],
    queryFn: async () => {
      const response = await apiClient.post<SessionPlan>(
        '/api/v1/workouts/recommend',
        {
          knee_pain: validPain,
          energy: validEnergy,
        }
      );
      return response.data;
    },
    retry: false, // Don't retry on 404
  });

  // Check if error is a 404 (no workout found)
  const is404Error =
    error &&
    'response' in error &&
    error.response &&
    'status' in error.response &&
    error.response.status === 404;

  return (
    <ScrollView className="flex-1 bg-gray-50">
      <View className="flex-1 p-6">
        {isLoading && (
          <View className="flex-1 items-center justify-center py-20">
            <ActivityIndicator size="large" color="#3b82f6" />
            <Text className="mt-4 text-gray-600 text-lg">
              Calculating your workout plan...
            </Text>
          </View>
        )}

        {is404Error && (
          <View className="flex-1 items-center justify-center py-20">
            <View className="bg-white rounded-lg shadow-lg p-8 items-center">
              <Text className="text-3xl font-bold text-gray-900 mb-3">
                Rest Day
              </Text>
              <Text className="text-gray-600 text-center mb-6">
                No workout recommended for your current readiness level
              </Text>
              <TouchableOpacity
                onPress={() => router.back()}
                className="bg-blue-600 px-6 py-3 rounded-lg"
              >
                <Text className="text-white font-semibold">Back to Check-In</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {error && !is404Error && (
          <View className="flex-1 items-center justify-center py-20">
            <View className="bg-white rounded-lg shadow-lg p-8 items-center">
              <Text className="text-xl font-bold text-red-600 mb-3">
                Error Loading Workout
              </Text>
              <Text className="text-gray-600 text-center mb-6">
                {error instanceof Error
                  ? error.message
                  : 'An unknown error occurred'}
              </Text>
              <TouchableOpacity
                onPress={() => refetch()}
                className="bg-blue-600 px-6 py-3 rounded-lg"
              >
                <Text className="text-white font-semibold">Retry</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {data && (
          <View className="bg-white rounded-lg shadow-lg p-6">
            <Text className="text-3xl font-bold text-gray-900 mb-2">
              {data.session_name}
            </Text>
            <Text className="text-lg text-gray-600 mb-4">{data.archetype}</Text>
            
            <View className="mb-6">
              <Text className="text-sm text-gray-500">
                Priority Score: {data.priority_score.toFixed(2)}
              </Text>
            </View>

            <View className="border-t border-gray-200 pt-4">
              <Text className="text-xl font-semibold text-gray-900 mb-4">
                Exercises
              </Text>
              {data.exercises.length > 0 ? (
                <View>
                  {data.exercises.map((exercise, index) => (
                    <View
                      key={index}
                      className="bg-gray-50 rounded-lg p-3 mb-2"
                    >
                      <Text className="text-gray-900">
                        {index + 1}. {exercise}
                      </Text>
                    </View>
                  ))}
                </View>
              ) : (
                <Text className="text-gray-500">No exercises listed</Text>
              )}
            </View>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

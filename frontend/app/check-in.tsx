import { useState } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { apiClient, ReadinessCheckInResponse } from '@/src/api/client';
import NumberSelector from '@/components/NumberSelector';

export default function CheckInScreen() {
  const router = useRouter();
  const [kneePain, setKneePain] = useState<number>(0);
  const [energy, setEnergy] = useState<number>(0);

  const mutation = useMutation<ReadinessCheckInResponse, Error, void>({
    mutationFn: async () => {
      const response = await apiClient.post<ReadinessCheckInResponse>(
        '/api/v1/readiness/check-in',
        {
          knee_pain: kneePain,
          energy: energy,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      // Navigate to workout plan with query parameters
      router.push(`/workout-plan?pain=${kneePain}&energy=${energy}`);
    },
  });

  const handleSubmit = () => {
    mutation.mutate();
  };

  return (
    <ScrollView className="flex-1 bg-gray-50">
      <View className="flex-1 p-6">
        <Text className="text-3xl font-bold text-gray-900 mb-8 text-center">
          Daily Readiness Check-In
        </Text>

        <View className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <NumberSelector
            label="Knee Pain (0-10)"
            value={kneePain}
            onChange={setKneePain}
          />
        </View>

        <View className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <NumberSelector
            label="Energy Level (0-10)"
            value={energy}
            onChange={setEnergy}
          />
        </View>

        {mutation.error && (
          <View className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <Text className="text-red-600 font-semibold mb-1">
              Error submitting check-in
            </Text>
            <Text className="text-red-500 text-sm">
              {mutation.error instanceof Error
                ? mutation.error.message
                : 'An unknown error occurred'}
            </Text>
          </View>
        )}

        <TouchableOpacity
          onPress={handleSubmit}
          disabled={mutation.isPending}
          className={`px-8 py-4 rounded-lg shadow-lg ${
            mutation.isPending
              ? 'bg-gray-400'
              : 'bg-blue-600 active:bg-blue-700'
          }`}
        >
          {mutation.isPending ? (
            <View className="flex-row items-center justify-center">
              <ActivityIndicator size="small" color="#ffffff" />
              <Text className="text-white text-lg font-semibold ml-2">
                Submitting...
              </Text>
            </View>
          ) : (
            <Text className="text-white text-lg font-semibold text-center">
              Submit
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

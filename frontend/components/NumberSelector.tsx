import { View, Text, TouchableOpacity } from 'react-native';

interface NumberSelectorProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
}

export default function NumberSelector({
  label,
  value,
  onChange,
}: NumberSelectorProps) {
  const numbers = Array.from({ length: 11 }, (_, i) => i); // 0-10

  return (
    <View className="mb-6">
      <Text className="text-lg font-semibold text-gray-900 mb-3">{label}</Text>
      <View className="flex-row flex-wrap gap-2">
        {numbers.map((num) => {
          const isSelected = num === value;
          return (
            <TouchableOpacity
              key={num}
              onPress={() => onChange(num)}
              className={`px-4 py-3 rounded-lg ${
                isSelected
                  ? 'bg-blue-600'
                  : 'bg-gray-200'
              }`}
            >
              <Text
                className={`text-lg font-semibold ${
                  isSelected ? 'text-white' : 'text-gray-700'
                }`}
              >
                {num}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
      {value !== undefined && (
        <Text className="text-sm text-gray-500 mt-2">Selected: {value}</Text>
      )}
    </View>
  );
}

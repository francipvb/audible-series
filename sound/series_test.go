package sound

import "testing"

func Test_calculateFreq(t *testing.T) {
	type args struct {
		minValue float64
		maxValue float64
		minFreq  float64
		maxFreq  float64
		v        float64
	}
	tests := []struct {
		name string
		args args
		want float64
	}{
		{
			name: "Regular case",
			args: args{
				minValue: 4,
				maxValue: 10,
				minFreq:  200,
				maxFreq:  800,
				v:        7,
			},
			want: 500,
		},
		{
			name: "Overflow on lower bound",
			args: args{
				minValue: 4,
				maxValue: 10,
				minFreq:  200,
				maxFreq:  800,
				v:        3.5,
			},
			want: 150,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := calculateFreq(tt.args.minValue, tt.args.maxValue, tt.args.minFreq, tt.args.maxFreq, tt.args.v); got != tt.want {
				t.Errorf("calculateFreq() = %v, want %v", got, tt.want)
			}
		})
	}
}

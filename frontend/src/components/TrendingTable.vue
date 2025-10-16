<template>
  <div class="trending-table">
    <table>
      <thead>
        <tr>
          <th rowspan="2">年份</th>
          <th v-for="month in months" :key="month">{{ month }}</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="year in years" :key="year">
          <tr>
            <td>{{ year }}</td>
            <template
              v-for="(value, monthIndex) in getYearData(year)"
              :key="year + '-month-' + monthIndex"
            >
              <td>{{ valueDisplay(value) }}</td>
            </template>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue';

export default {
  name: 'TrendingTable',
  props: {
    data: {
      type: Object,
      required: true
    }
  },
  setup(props) {
    const yearData = ref({});

    const months = computed(() => [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]);

    const years = computed(() => {
      const startYear = new Date(props.data.時間起點).getFullYear();
      const endYear = new Date(props.data.時間終點).getFullYear();
      const result = [];
      for (let y = startYear; y <= endYear; y++) {
        result.push(y);
      }
      return result;
    });

    const processInitData = () => {
      const startMonth = new Date(props.data.時間起點).getMonth() + 1;
      const endMonth = new Date(props.data.時間終點).getMonth() + 1;
      const startYear = new Date(props.data.時間起點).getFullYear();
      const endYear = new Date(props.data.時間終點).getFullYear();
      const rawPrices = props.data.統計值.split(',');

      const result = {};
      let index = 0;

      for (let year = startYear; year <= endYear; year++) {
        const yearPrices = [];
        for (let month = 1; month <= 12; month++) {
          if (year === startYear && month < startMonth) {
            yearPrices.push('0');
          } else if (year === endYear && month > endMonth) {
            yearPrices.push('0');
          } else {
            yearPrices.push(rawPrices[index] || '0');
            index++;
          }
        }
        result[year] = yearPrices;
      }

      yearData.value = result;
    };

    const getYearData = year => yearData.value[year] || [];

    const valueDisplay = value => (value === '0' ? '-' : value);

    watch(() => props.data, processInitData, { deep: true });
    onMounted(processInitData);

    return {
      months,
      years,
      getYearData,
      valueDisplay
    };
  }
};
</script>

<style scoped>
.trending-table {
  margin-top: 2em;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border: 1px solid #ccc;
  padding: 0.5em;
  text-align: center;
}
</style>

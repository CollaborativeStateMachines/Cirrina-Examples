Vagrant.configure("2") do |config|
  nodes = {
    "counter" => { "RUN" => "counter" },
    "producer" => { "RUN" => "producer" }
  }

  nodes.each do |name, env_vars|
    config.vm.define name do |node|
      influx_metric_url = ENV['INFLUX_METRIC_URL']
      node.vm.box = "generic/ubuntu2004"

      ip_suffix = name == "producer" ? 10 : 11
      node.vm.network "private_network", ip: "192.168.56.#{ip_suffix}"
      node.vm.synced_folder "./count", "/app/count"

      node.vm.provision "shell", inline: <<-SHELL
        apt-get update -qq && apt-get install -y docker.io
        
        docker rm -f #{name} || true

        docker run -d \
          --name #{name} \
          --network host \
          -e RUN=#{env_vars['RUN']} \
          -e INFLUX_METRIC_URL=#{influx_metric_url} \
          -e METRICS_DIRECTORY="/app/run/metrics_#{name}" \
          -v /app/count:/app \
          collaborativestatemachines/cirrina:unstable
      SHELL
    end
  end
end
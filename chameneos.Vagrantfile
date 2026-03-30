Vagrant.configure("2") do |config|
  nodes = {
    "mall" => { "RUN" => "mall" },
    "w0" => { "RUN" => "0" }, "w1" => { "RUN" => "1" },
    "w2" => { "RUN" => "2" }, "w3" => { "RUN" => "3" },
    "w4" => { "RUN" => "4" }, "w5" => { "RUN" => "5" },
    "w6" => { "RUN" => "6" }, "w7" => { "RUN" => "7" },
    "w8" => { "RUN" => "8" }, "w9" => { "RUN" => "9" },
    "w10" => { "RUN" => "10" }, "w11" => { "RUN" => "11" }
  }

  nodes.each do |name, env_vars|
    config.vm.define name do |node|
      influx_metric_url = ENV['INFLUX_METRIC_URL']
      node.vm.box = "generic/ubuntu2004"

      ip_suffix = name == "mall" ? 10 : 11 + name[1..-1].to_i
      node.vm.network "private_network", ip: "192.168.56.#{ip_suffix}"
      node.vm.synced_folder "./chameneos", "/app/chameneos"

      node.vm.provision "shell", inline: <<-SHELL
        apt-get update -qq && apt-get install -y docker.io
        
        docker rm -f #{name} || true

        docker run -d \
          --name #{name} \
          --network host \
          -e RUN=#{env_vars['RUN']} \
          -e INFLUX_METRIC_URL=#{influx_metric_url} \
          -e METRICS_DIRECTORY="/app/run/metrics_#{name}" \
          -v /app/chameneos:/app \
          collaborativestatemachines/cirrina:unstable
      SHELL
    end
  end
end